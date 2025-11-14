package backend

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/rs/zerolog"
)

// Identity exposes registration-related endpoints of the backend.
type Identity interface {
	Universities(ctx context.Context) ([]University, error)
	Faculties(ctx context.Context, universityID string) ([]Faculty, error)
	Groups(ctx context.Context, universityID, facultyID string) ([]Group, error)
	Kafedras(ctx context.Context, universityID, facultyID string) ([]Kafedra, error)
	Register(ctx context.Context, req RegistrationRequest) (RegistrationResult, error)
}

type University struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	City string `json:"city"`
}

type Faculty struct {
	ID    string `json:"id"`
	Title string `json:"title"`
}

type Group struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Code string `json:"code"`
}

type Kafedra struct {
	ID    string `json:"id"`
	Title string `json:"title"`
}

type UserRole string

const (
	UserRoleStudent UserRole = "student"
	UserRoleStaff   UserRole = "staff"
)

type RegistrationRequest struct {
	MaxID        int64
	Role         UserRole
	FullName     string
	City         string
	UniversityID string
	FacultyID    string
	GroupID      string
	StudentCard  string
	KafedraID    string
	TabNumber    string
}

type RegistrationResult struct {
	UserID      string
	AccessToken string
	Message     string
}

func NewIdentity(baseURL string, log zerolog.Logger) (Identity, error) {
	base := strings.TrimSpace(baseURL)
	if base == "" {
		return newStubIdentity(), nil
	}
	if !strings.Contains(base, "://") {
		base = "http://" + base
	}
	u, err := url.Parse(base)
	if err != nil {
		return nil, fmt.Errorf("identity backend: parse base url: %w", err)
	}
	u.RawQuery = ""
	u.Fragment = ""
	clean := strings.TrimRight(u.String(), "/")
	if clean == "" {
		return nil, errors.New("identity backend: resolved base url is empty")
	}
	return &httpIdentity{
		baseURL: clean,
		client:  &http.Client{Timeout: 10 * time.Second},
		log:     log.With().Str("component", "identity-backend").Logger(),
	}, nil
}

type httpIdentity struct {
	baseURL string
	client  *http.Client
	log     zerolog.Logger
}

func (i *httpIdentity) Universities(ctx context.Context) ([]University, error) {
	var list []University
	if err := i.doRequest(ctx, http.MethodGet, "/universities", nil, &list); err != nil {
		return nil, err
	}
	return list, nil
}

func (i *httpIdentity) Faculties(ctx context.Context, universityID string) ([]Faculty, error) {
	path := fmt.Sprintf("/universities/%s/faculties", universityID)
	var list []Faculty
	if err := i.doRequest(ctx, http.MethodGet, path, nil, &list); err != nil {
		return nil, err
	}
	return list, nil
}

func (i *httpIdentity) Groups(ctx context.Context, universityID, facultyID string) ([]Group, error) {
	path := fmt.Sprintf("/universities/%s/faculties/%s/groups", universityID, facultyID)
	var list []Group
	if err := i.doRequest(ctx, http.MethodGet, path, nil, &list); err != nil {
		return nil, err
	}
	return list, nil
}

func (i *httpIdentity) Kafedras(ctx context.Context, universityID, facultyID string) ([]Kafedra, error) {
	path := fmt.Sprintf("/universities/%s/faculties/%s/kafedras", universityID, facultyID)
	var list []Kafedra
	if err := i.doRequest(ctx, http.MethodGet, path, nil, &list); err != nil {
		return nil, err
	}
	return list, nil
}

func (i *httpIdentity) Register(ctx context.Context, req RegistrationRequest) (RegistrationResult, error) {
	payload := map[string]interface{}{
		"max_id":        req.MaxID,
		"role":          req.Role,
		"full_name":     req.FullName,
		"city":          req.City,
		"university_id": req.UniversityID,
	}
	if req.FacultyID != "" {
		payload["faculty_id"] = req.FacultyID
	}
	if req.GroupID != "" {
		payload["group_id"] = req.GroupID
	}
	if req.StudentCard != "" {
		payload["student_card"] = req.StudentCard
	}
	if req.KafedraID != "" {
		payload["kafedra_id"] = req.KafedraID
	}
	if req.TabNumber != "" {
		payload["tab_number"] = req.TabNumber
	}

	var resp registrationResponse
	if err := i.doRequest(ctx, http.MethodPost, "/auth/register", payload, &resp); err != nil {
		return RegistrationResult{}, err
	}
	if strings.TrimSpace(resp.UserID) == "" {
		return RegistrationResult{}, errors.New("identity backend returned empty user id")
	}
	return RegistrationResult{
		UserID:      resp.UserID,
		AccessToken: resp.AccessToken,
		Message:     resp.Message,
	}, nil
}

func (i *httpIdentity) doRequest(ctx context.Context, method, path string, body interface{}, out interface{}) error {
	fullURL := fmt.Sprintf("%s%s", i.baseURL, path)

	var buf *bytes.Buffer
	if body != nil {
		buf = &bytes.Buffer{}
		if err := json.NewEncoder(buf).Encode(body); err != nil {
			return fmt.Errorf("identity backend: encode request: %w", err)
		}
	}
	var reader io.Reader
	if buf != nil {
		reader = buf
	}

	req, err := http.NewRequestWithContext(ctx, method, fullURL, reader)
	if err != nil {
		return fmt.Errorf("identity backend: build request: %w", err)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := i.client.Do(req)
	if err != nil {
		return fmt.Errorf("identity backend: request failed: %w", err)
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
		return fmt.Errorf("identity backend: decode response: %w", err)
	}
	return nil
}

type registrationResponse struct {
	Success     bool   `json:"success"`
	Message     string `json:"message"`
	UserID      string `json:"user_id"`
	AccessToken string `json:"access_token"`
}

type stubIdentity struct{}

func newStubIdentity() Identity {
	return stubIdentity{}
}

func (stubIdentity) Universities(context.Context) ([]University, error) {
	return []University{
		{ID: "stub-uni-1", Name: "Demo University", City: "Mock City"},
	}, nil
}

func (stubIdentity) Faculties(_ context.Context, universityID string) ([]Faculty, error) {
	if universityID == "" {
		return nil, nil
	}
	return []Faculty{
		{ID: "stub-fac-1", Title: "Engineering"},
		{ID: "stub-fac-2", Title: "Humanities"},
	}, nil
}

func (stubIdentity) Groups(_ context.Context, universityID, facultyID string) ([]Group, error) {
	if universityID == "" || facultyID == "" {
		return nil, nil
	}
	return []Group{
		{ID: "stub-group-1", Name: "101", Code: "101"},
		{ID: "stub-group-2", Name: "201", Code: "201"},
	}, nil
}

func (stubIdentity) Kafedras(_ context.Context, universityID, facultyID string) ([]Kafedra, error) {
	if universityID == "" || facultyID == "" {
		return nil, nil
	}
	return []Kafedra{
		{ID: "stub-kaf-1", Title: "Applied Math"},
		{ID: "stub-kaf-2", Title: "Physics"},
	}, nil
}

func (stubIdentity) Register(_ context.Context, req RegistrationRequest) (RegistrationResult, error) {
	return RegistrationResult{
		UserID:      fmt.Sprintf("stub-user-%d", req.MaxID),
		AccessToken: "stub-token",
		Message:     "demo registration complete",
	}, nil
}

var _ Identity = (*httpIdentity)(nil)
var _ Identity = (*stubIdentity)(nil)
