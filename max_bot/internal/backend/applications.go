package backend

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/url"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/max-messenger/max-bot-api-client-go/schemes"
	"github.com/rs/zerolog"
)

// Role определяет тип пользователя в контексте заявок.
type Role string

// ApplicationType описывает доступные типы заявок.
type ApplicationType string

const (
	attachmentDownloadLimit = 25 << 20 // 25 MB

	RoleStudent Role = "student"
	RoleTeacher Role = "teacher"

	ApplicationTypeStudyCertificate ApplicationType = "study_certificate"
	ApplicationTypeAcademicLeave    ApplicationType = "academic_leave"
	ApplicationTypeStudyTransfer    ApplicationType = "study_transfer"
	ApplicationTypeWorkCertificate  ApplicationType = "work_certificate"
)

// Applications определяет контракт общения с backend для заявок.
type Applications interface {
	ResolveRole(ctx context.Context, userID int64) (Role, error)
	SubmitApplication(ctx context.Context, userID int64, role Role, docType ApplicationType, payload map[string]string) error
}

// MockApplications расширяет контракт хранением загруженных файлов (используется в e2e).
type MockApplications interface {
	Applications
	StoredFiles(userID int64) map[string][]schemes.FileAttachment
}

// NewApplications возвращает HTTP-бэкенд или встроенный стаб, если baseURL пуст.
func NewApplications(baseURL string, log zerolog.Logger) (Applications, error) {
	if strings.TrimSpace(baseURL) == "" {
		return newStubApplications(log), nil
	}
	return newHTTPApplications(baseURL, log)
}

type httpApplications struct {
	baseURL string
	client  *http.Client
	log     zerolog.Logger
}

func newHTTPApplications(baseURL string, log zerolog.Logger) (*httpApplications, error) {
	base := strings.TrimSpace(baseURL)
	if base == "" {
		return nil, errors.New("application backend: base url is empty")
	}
	if !strings.Contains(base, "://") {
		base = "http://" + base
	}
	parsed, err := url.Parse(base)
	if err != nil {
		return nil, fmt.Errorf("application backend: parse base url: %w", err)
	}
	parsed.RawQuery = ""
	parsed.Fragment = ""
	cleaned := strings.TrimRight(parsed.String(), "/")
	if cleaned == "" {
		return nil, errors.New("application backend: resolved base url is empty")
	}

	return &httpApplications{
		baseURL: cleaned,
		client:  &http.Client{Timeout: 10 * time.Second},
		log:     log.With().Str("component", "application-backend").Logger(),
	}, nil
}

func (b *httpApplications) ResolveRole(ctx context.Context, userID int64) (Role, error) {
	token, err := b.login(ctx, userID)
	if err != nil {
		return "", err
	}

	var resp profileResponse
	if err := b.doRequest(ctx, http.MethodGet, "/users/profile", nil, token, &resp); err != nil {
		return "", err
	}
	role, err := mapBackendRole(resp.Role)
	if err != nil {
		return "", err
	}
	return role, nil
}

func (b *httpApplications) SubmitApplication(ctx context.Context, userID int64, role Role, docType ApplicationType, payload map[string]string) error {
	token, err := b.login(ctx, userID)
	if err != nil {
		return err
	}

	requestType, ok := applicationRequestType[docType]
	if !ok {
		return fmt.Errorf("unsupported application type %q", docType)
	}

	content := buildRequestContent(docType, payload, b.log)
	body := requestCreate{
		RequestType: requestType,
		Content:     content,
	}
	var created requestCreateResponse
	if err := b.doRequest(ctx, http.MethodPost, "/requests", body, token, &created); err != nil {
		return err
	}

	if docType == ApplicationTypeAcademicLeave {
		if err := b.uploadAcademicLeaveDocuments(ctx, created.ID, payload, token); err != nil {
			return err
		}
	}
	return nil
}

func (b *httpApplications) login(ctx context.Context, userID int64) (string, error) {
	path := fmt.Sprintf("/auth/login-by-max-id?max_id=%d", userID)
	var resp tokenResponse
	if err := b.doRequest(ctx, http.MethodGet, path, nil, "", &resp); err != nil {
		var httpErr *HTTPError
		if errors.As(err, &httpErr) && httpErr.StatusCode == http.StatusNotFound {
			return "", ErrUserNotFound
		}
		return "", err
	}
	token := strings.TrimSpace(resp.AccessToken)
	if token == "" {
		return "", errors.New("backend returned empty access token")
	}
	return token, nil
}

func (b *httpApplications) doRequest(ctx context.Context, method, path string, body interface{}, token string, out interface{}) error {
	fullURL := fmt.Sprintf("%s%s", b.baseURL, path)

	var reqBody *bytes.Buffer
	if body != nil {
		reqBody = &bytes.Buffer{}
		if err := json.NewEncoder(reqBody).Encode(body); err != nil {
			return fmt.Errorf("encode request body: %w", err)
		}
	}

	var reader io.Reader
	if reqBody != nil {
		reader = reqBody
	}

	req, err := http.NewRequestWithContext(ctx, method, fullURL, reader)
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := b.client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= http.StatusBadRequest {
		snippet, _ := io.ReadAll(io.LimitReader(resp.Body, 1024))
		return &HTTPError{
			Method:     method,
			Path:       path,
			StatusCode: resp.StatusCode,
			Body:       strings.TrimSpace(string(snippet)),
		}
	}

	if out == nil {
		_, _ = io.Copy(io.Discard, resp.Body)
		return nil
	}

	if err := json.NewDecoder(resp.Body).Decode(out); err != nil {
		return fmt.Errorf("decode backend response: %w", err)
	}
	return nil
}

type tokenResponse struct {
	AccessToken string `json:"access_token"`
}

type profileResponse struct {
	Role string `json:"role"`
}

type requestCreate struct {
	RequestType string `json:"request_type"`
	Content     string `json:"content,omitempty"`
}

type requestCreateResponse struct {
	ID int `json:"id"`
}

func mapBackendRole(value string) (Role, error) {
	role := strings.ToLower(strings.TrimSpace(value))
	switch role {
	case "student":
		return RoleStudent, nil
	case "teacher", "staff", "admin":
		return RoleTeacher, nil
	default:
		return "", fmt.Errorf("unsupported backend role %q", value)
	}
}

func buildRequestContent(docType ApplicationType, payload map[string]string, log zerolog.Logger) string {
	title := applicationTitles[docType]
	if title == "" {
		title = string(docType)
	}
	var b strings.Builder
	fmt.Fprintf(&b, "Заявка: %s\n", title)
	if len(payload) == 0 {
		b.WriteString("Дополнительные данные не заполнялись.")
		return b.String()
	}

	keys := make([]string, 0, len(payload))
	for key := range payload {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	b.WriteString("\nПоля:\n")
	for i, key := range keys {
		label := fieldLabels[key]
		if label == "" {
			label = key
		}
		value := formatFieldValue(key, payload[key], log)
		fmt.Fprintf(&b, "%d) %s: %s\n", i+1, label, value)
	}

	return strings.TrimSpace(b.String())
}

func (b *httpApplications) uploadAcademicLeaveDocuments(ctx context.Context, requestID int, payload map[string]string, token string) error {
	if requestID <= 0 {
		return fmt.Errorf("application backend: invalid request id")
	}
	raw := strings.TrimSpace(payload["supporting_files"])
	if raw == "" {
		return fmt.Errorf("application backend: supporting files are required for academic leave")
	}
	files := decodeFileAttachmentPayload("supporting_files", raw, b.log)
	if len(files) == 0 {
		return fmt.Errorf("application backend: failed to decode supporting files")
	}
	for _, file := range files {
		data, err := b.downloadAttachment(ctx, file.Payload.Url)
		if err != nil {
			return fmt.Errorf("application backend: download attachment %q: %w", file.Filename, err)
		}
		if err := b.sendRequestDocument(ctx, requestID, token, file, data); err != nil {
			return err
		}
	}
	return nil
}

func (b *httpApplications) downloadAttachment(ctx context.Context, fileURL string) ([]byte, error) {
	url := strings.TrimSpace(fileURL)
	if url == "" {
		return nil, fmt.Errorf("attachment url is empty")
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("build attachment request: %w", err)
	}
	resp, err := b.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("download attachment: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= http.StatusBadRequest {
		return nil, fmt.Errorf("download attachment failed: %s", resp.Status)
	}
	reader := io.LimitReader(resp.Body, attachmentDownloadLimit)
	data, err := io.ReadAll(reader)
	if err != nil {
		return nil, fmt.Errorf("read attachment: %w", err)
	}
	return data, nil
}

func (b *httpApplications) sendRequestDocument(ctx context.Context, requestID int, token string, file schemes.FileAttachment, data []byte) error {
	var body bytes.Buffer
	writer := multipart.NewWriter(&body)
	filename := strings.TrimSpace(file.Filename)
	if filename == "" {
		filename = fmt.Sprintf("document-%d.dat", time.Now().UnixNano())
	}
	part, err := writer.CreateFormFile("file", filename)
	if err != nil {
		return fmt.Errorf("application backend: create form file: %w", err)
	}
	if _, err := part.Write(data); err != nil {
		return fmt.Errorf("application backend: write attachment: %w", err)
	}
	if err := writer.Close(); err != nil {
		return fmt.Errorf("application backend: finalize multipart: %w", err)
	}
	endpoint := fmt.Sprintf("%s/requests/%d/documents", b.baseURL, requestID)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, &body)
	if err != nil {
		return fmt.Errorf("application backend: build document request: %w", err)
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := b.client.Do(req)
	if err != nil {
		return fmt.Errorf("application backend: upload document: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= http.StatusBadRequest {
		snippet, _ := io.ReadAll(io.LimitReader(resp.Body, 1024))
		return fmt.Errorf("application backend: upload document failed (%s): %s", resp.Status, strings.TrimSpace(string(snippet)))
	}
	return nil
}

func formatFieldValue(field, value string, log zerolog.Logger) string {
	v := strings.TrimSpace(value)
	if v == "" {
		return "не указано"
	}
	if strings.HasPrefix(v, "[") {
		files := decodeFileAttachmentPayload(field, v, log)
		if len(files) == 0 {
			return "прикреплены файлы (см. MAX)"
		}
		parts := make([]string, 0, len(files))
		for _, f := range files {
			parts = append(parts, fmt.Sprintf("%s (token %s)", f.Filename, f.Payload.Token))
		}
		return "вложения: " + strings.Join(parts, "; ")
	}
	return v
}

var applicationRequestType = map[ApplicationType]string{
	ApplicationTypeStudyCertificate: "student_certificate",
	ApplicationTypeAcademicLeave:    "academic_leave",
	ApplicationTypeStudyTransfer:    "transfer",
	ApplicationTypeWorkCertificate:  "document_approval",
}

var applicationTitles = map[ApplicationType]string{
	ApplicationTypeStudyCertificate: "Справка с места учебы",
	ApplicationTypeAcademicLeave:    "Академический отпуск",
	ApplicationTypeStudyTransfer:    "Перевод на другую программу",
	ApplicationTypeWorkCertificate:  "Справка по месту работы",
}

var fieldLabels = map[string]string{
	"supporting_files": "Подтверждающие документы",
	"reason_text":      "Причина",
	"gradebook_copy":   "Копия зачетной книжки",
	"target_program":   "Желаемая программа/направление",
}

type stubApplications struct {
	log         zerolog.Logger
	mu          sync.Mutex
	submissions map[int64]map[string][]schemes.FileAttachment
}

func newStubApplications(log zerolog.Logger) *stubApplications {
	return &stubApplications{
		log:         log.With().Str("component", "documents-mock").Logger(),
		submissions: make(map[int64]map[string][]schemes.FileAttachment),
	}
}

func (s *stubApplications) ResolveRole(_ context.Context, userID int64) (Role, error) {
	if userID%2 == 0 {
		return RoleStudent, nil
	}
	return RoleTeacher, nil
}

func (s *stubApplications) SubmitApplication(_ context.Context, userID int64, role Role, docType ApplicationType, payload map[string]string) error {
	s.log.Info().
		Int64("user_id", userID).
		Str("role", string(role)).
		Str("doc_type", string(docType)).
		Msg("mock document submission")

	attachments := s.extractAttachments(payload)
	if len(attachments) == 0 {
		return nil
	}

	s.mu.Lock()
	s.submissions[userID] = attachments
	s.mu.Unlock()
	return nil
}

func (s *stubApplications) StoredFiles(userID int64) map[string][]schemes.FileAttachment {
	s.mu.Lock()
	defer s.mu.Unlock()
	files, ok := s.submissions[userID]
	if !ok {
		return nil
	}
	copy := make(map[string][]schemes.FileAttachment, len(files))
	for field, list := range files {
		copy[field] = append([]schemes.FileAttachment(nil), list...)
	}
	return copy
}

func (s *stubApplications) extractAttachments(payload map[string]string) map[string][]schemes.FileAttachment {
	result := make(map[string][]schemes.FileAttachment)
	for field, rawValue := range payload {
		data := strings.TrimSpace(rawValue)
		if data == "" || !strings.HasPrefix(data, "[") {
			continue
		}
		files := decodeFileAttachmentPayload(field, data, s.log)
		if len(files) == 0 {
			continue
		}
		result[field] = files
	}
	return result
}

func decodeFileAttachmentPayload(field, data string, log zerolog.Logger) []schemes.FileAttachment {
	data = strings.TrimSpace(data)
	if data == "" {
		return nil
	}

	var items []json.RawMessage
	if err := json.Unmarshal([]byte(data), &items); err != nil {
		log.Debug().Err(err).Str("field", field).Msg("mock backend failed to parse attachment array")
		return nil
	}

	var attachments []schemes.FileAttachment
	for _, item := range items {
		var file schemes.FileAttachment
		if err := json.Unmarshal(item, &file); err != nil {
			log.Debug().Err(err).Msg("mock backend failed to decode attachment")
			continue
		}
		if file.Filename == "" {
			log.Debug().Msg("mock backend skipping attachment without filename")
			continue
		}
		log.Info().
			Str("field", field).
			Str("filename", file.Filename).
			Int64("size", file.Size).
			Str("token", file.Payload.Token).
			Msg("mock backend received file payload")
		attachments = append(attachments, file)
	}
	return attachments
}

var _ Applications = (*httpApplications)(nil)
var _ Applications = (*stubApplications)(nil)
var _ MockApplications = (*stubApplications)(nil)
