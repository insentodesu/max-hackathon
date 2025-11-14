package backend

import (
	"fmt"
	"net/http"
	"strings"
)

// ErrUserNotFound is returned when backend does not recognize the MAX user.
var ErrUserNotFound = fmt.Errorf("backend: user is not registered")

type HTTPError struct {
	Method     string
	Path       string
	StatusCode int
	Body       string
}

func (e *HTTPError) Error() string {
	if e == nil {
		return ""
	}
	body := strings.TrimSpace(e.Body)
	if body == "" {
		body = http.StatusText(e.StatusCode)
	}
	return fmt.Sprintf("backend %s %s returned %d: %s", e.Method, e.Path, e.StatusCode, body)
}
