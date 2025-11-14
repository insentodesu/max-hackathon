package app

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"strings"

	"github.com/insentodesu/max_bot/internal/backend"
)

type registrationCoordinator struct {
	identity backend.Identity
}

func newRegistrationCoordinator(identity backend.Identity) (*registrationCoordinator, error) {
	if identity == nil {
		return nil, errors.New("registration coordinator: identity backend is nil")
	}
	return &registrationCoordinator{identity: identity}, nil
}

func (c *registrationCoordinator) LoadOptions(ctx context.Context, data *registrationSessionData) error {
	if c.identity == nil {
		return errors.New("registration coordinator: identity backend is not configured")
	}
	switch data.Step {
	case registrationStepUniversity:
		universities, err := c.identity.Universities(ctx)
		if err != nil {
			return fmt.Errorf("не удалось загрузить список университетов: %w", err)
		}
		if len(universities) == 0 {
			return errors.New("в каталоге пока нет университетов")
		}
		opts := make([]registrationOption, 0, len(universities))
		for _, uni := range universities {
			opts = append(opts, registrationOption{
				ID:       uni.ID,
				Title:    uni.Name,
				Subtitle: uni.City,
			})
		}
		data.setOptions(opts)
	case registrationStepFaculty:
		if data.University.ID == "" {
			return errors.New("сначала выберите университет")
		}
		faculties, err := c.identity.Faculties(ctx, data.University.ID)
		if err != nil {
			return fmt.Errorf("не удалось получить список факультетов: %w", err)
		}
		if len(faculties) == 0 {
			return errors.New("в университете пока нет факультетов")
		}
		opts := make([]registrationOption, 0, len(faculties))
		for _, fac := range faculties {
			opts = append(opts, registrationOption{
				ID:    fac.ID,
				Title: fac.Title,
			})
		}
		data.setOptions(opts)
	case registrationStepGroup:
		if data.University.ID == "" || data.Faculty.ID == "" {
			return errors.New("сначала выберите факультет")
		}
		groups, err := c.identity.Groups(ctx, data.University.ID, data.Faculty.ID)
		if err != nil {
			return fmt.Errorf("не удалось получить список групп: %w", err)
		}
		if len(groups) == 0 {
			return errors.New("для выбранного факультета нет учебных групп")
		}
		opts := make([]registrationOption, 0, len(groups))
		for _, grp := range groups {
			opts = append(opts, registrationOption{
				ID:       grp.ID,
				Title:    grp.Name,
				Subtitle: grp.Code,
			})
		}
		data.setOptions(opts)
	case registrationStepKafedra:
		if data.University.ID == "" || data.Faculty.ID == "" {
			return errors.New("сначала выберите факультет")
		}
		kafedras, err := c.identity.Kafedras(ctx, data.University.ID, data.Faculty.ID)
		if err != nil {
			return fmt.Errorf("не удалось получить список кафедр: %w", err)
		}
		if len(kafedras) == 0 {
			return errors.New("для выбранного факультета пока нет кафедр")
		}
		opts := make([]registrationOption, 0, len(kafedras))
		for _, k := range kafedras {
			opts = append(opts, registrationOption{
				ID:    k.ID,
				Title: k.Title,
			})
		}
		data.setOptions(opts)
	default:
		data.clearOptions()
	}
	return nil
}

func (c *registrationCoordinator) Register(ctx context.Context, userID int64, data registrationSessionData) (backend.RegistrationResult, error) {
	if c.identity == nil {
		return backend.RegistrationResult{}, errors.New("registration coordinator: identity backend is not configured")
	}
	if userID <= 0 {
		return backend.RegistrationResult{}, errors.New("registration невозможна: неизвестен user id")
	}
	if data.FullName == "" {
		return backend.RegistrationResult{}, errors.New("укажите ФИО")
	}
	if data.University.ID == "" || data.University.Name == "" {
		return backend.RegistrationResult{}, errors.New("выберите университет")
	}

	req := backend.RegistrationRequest{
		MaxID:        userID,
		Role:         data.Role,
		FullName:     data.FullName,
		City:         data.University.City,
		UniversityID: data.University.ID,
	}

	switch data.Role {
	case backend.UserRoleStudent:
		if data.Faculty.ID == "" {
			return backend.RegistrationResult{}, errors.New("выберите факультет")
		}
		if data.Group.ID == "" {
			return backend.RegistrationResult{}, errors.New("выберите учебную группу")
		}
		if strings.TrimSpace(data.StudentCard) == "" {
			return backend.RegistrationResult{}, errors.New("укажите номер студенческого")
		}
		req.FacultyID = data.Faculty.ID
		req.GroupID = data.Group.ID
		req.StudentCard = strings.TrimSpace(data.StudentCard)
	case backend.UserRoleStaff:
		if data.Faculty.ID == "" {
			return backend.RegistrationResult{}, errors.New("выберите факультет")
		}
		if data.Kafedra.ID == "" {
			return backend.RegistrationResult{}, errors.New("выберите кафедру")
		}
		if strings.TrimSpace(data.TabNumber) == "" {
			return backend.RegistrationResult{}, errors.New("укажите табельный номер")
		}
		req.FacultyID = data.Faculty.ID
		req.KafedraID = data.Kafedra.ID
		req.TabNumber = strings.TrimSpace(data.TabNumber)
	default:
		return backend.RegistrationResult{}, fmt.Errorf("поддерживаются только роли %q и %q", backend.UserRoleStudent, backend.UserRoleStaff)
	}

	return c.identity.Register(ctx, req)
}

type registrationStep string

const (
	registrationStepFullName    registrationStep = "full_name"
	registrationStepUniversity  registrationStep = "university"
	registrationStepFaculty     registrationStep = "faculty"
	registrationStepGroup       registrationStep = "group"
	registrationStepStudentCard registrationStep = "student_card"
	registrationStepKafedra     registrationStep = "kafedra"
	registrationStepTabNumber   registrationStep = "tab_number"
)

type registrationOption struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	Subtitle string `json:"subtitle,omitempty"`
}

type registrationSessionData struct {
	Role        backend.UserRole       `json:"role"`
	Step        registrationStep       `json:"step"`
	FullName    string                 `json:"full_name"`
	University  registrationUniversity `json:"university"`
	Faculty     registrationEntity     `json:"faculty"`
	Group       registrationGroup      `json:"group"`
	Kafedra     registrationEntity     `json:"kafedra"`
	StudentCard string                 `json:"student_card"`
	TabNumber   string                 `json:"tab_number"`
	Options     []registrationOption   `json:"options,omitempty"`
}

type registrationUniversity struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	City string `json:"city"`
}

type registrationEntity struct {
	ID    string `json:"id"`
	Title string `json:"title"`
}

type registrationGroup struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Code string `json:"code"`
}

func newRegistrationSession(role backend.UserRole) registrationSessionData {
	return registrationSessionData{
		Role: role,
		Step: registrationStepFullName,
	}
}

func registrationSessionFromPayload(payload []byte) (registrationSessionData, error) {
	if len(payload) == 0 {
		return registrationSessionData{}, errors.New("registration session payload is empty")
	}
	var data registrationSessionData
	if err := json.Unmarshal(payload, &data); err != nil {
		return registrationSessionData{}, err
	}
	return data, nil
}

func (d *registrationSessionData) marshal() ([]byte, error) {
	return json.Marshal(d)
}

func (d *registrationSessionData) clearOptions() {
	d.Options = nil
}

func (d *registrationSessionData) setOptions(opts []registrationOption) {
	d.Options = append([]registrationOption(nil), opts...)
}

func (d *registrationSessionData) selectOption(input string) (registrationOption, error) {
	if len(d.Options) == 0 {
		return registrationOption{}, errors.New("нет доступных вариантов")
	}
	value := strings.TrimSpace(input)
	if value == "" {
		return registrationOption{}, errors.New("укажите номер варианта")
	}
	if idx, err := strconv.Atoi(value); err == nil {
		idx--
		if idx >= 0 && idx < len(d.Options) {
			return d.Options[idx], nil
		}
	}
	for _, opt := range d.Options {
		if strings.EqualFold(opt.ID, value) || strings.EqualFold(opt.Title, value) {
			return opt, nil
		}
	}
	return registrationOption{}, errors.New("вариант не найден")
}

func formatRegistrationOptions(opts []registrationOption) string {
	if len(opts) == 0 {
		return ""
	}
	var b strings.Builder
	for i, opt := range opts {
		fmt.Fprintf(&b, "%d. %s", i+1, opt.Title)
		if opt.Subtitle != "" {
			fmt.Fprintf(&b, " (%s)", opt.Subtitle)
		}
		if i < len(opts)-1 {
			b.WriteByte('\n')
		}
	}
	return b.String()
}
