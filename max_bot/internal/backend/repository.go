package backend

import "github.com/rs/zerolog"

// Repository агрегирует все backend-сервисы бота.
type Repository interface {
	Applications() Applications
	Payments() Payments
	Schedule() Schedule
	Identity() Identity
}

type repository struct {
	applications Applications
	payments     Payments
	schedule     Schedule
	identity     Identity
}

// NewRepository подготавливает все клиенты backend-а (или стабы при пустом baseURL).
func NewRepository(baseURL string, log zerolog.Logger) (Repository, error) {
	apps, err := NewApplications(baseURL, log)
	if err != nil {
		return nil, err
	}

	payments, err := NewPayments(baseURL, log)
	if err != nil {
		return nil, err
	}

	schedule, err := NewSchedule(baseURL, log)
	if err != nil {
		return nil, err
	}

	identity, err := NewIdentity(baseURL, log)
	if err != nil {
		return nil, err
	}

	return &repository{
		applications: apps,
		payments:     payments,
		schedule:     schedule,
		identity:     identity,
	}, nil
}

func (r *repository) Applications() Applications {
	return r.applications
}

func (r *repository) Payments() Payments {
	return r.payments
}

func (r *repository) Schedule() Schedule {
	return r.schedule
}

func (r *repository) Identity() Identity {
	return r.identity
}

var _ Repository = (*repository)(nil)
