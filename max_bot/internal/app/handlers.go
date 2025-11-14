package app

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"strings"

	"github.com/insentodesu/max_bot/internal/appbot"
	"github.com/insentodesu/max_bot/internal/backend"
	maxbot "github.com/max-messenger/max-bot-api-client-go"
	"github.com/max-messenger/max-bot-api-client-go/schemes"
)

const (
	menuRoot                = "menu:root"
	menuSchedule            = "menu:schedule"
	menuApplicationsStudent = "menu:applications:student"
	menuApplicationsTeacher = "menu:applications:teacher"

	actionPaymentRequestOrder             = "action:payment:request_order"
	actionPaymentDormPay                  = "action:payment:pay_dorm"
	actionPaymentTuitionPay               = "action:payment:pay_tuition"
	actionScheduleToday                   = "action:schedule:today"
	actionScheduleWeek                    = "action:schedule:week"
	actionApplicationsOpen                = "action:applications:open"
	actionApplicationStudentStudyCert     = "action:application:student:study_certificate"
	actionApplicationStudentAcademicLeave = "action:application:student:academic_leave"
	actionApplicationStudentTransfer      = "action:application:student:study_transfer"
	actionApplicationTeacherWorkCert      = "action:application:teacher:work_certificate"
	actionApplicationCancel               = "action:application:cancel"
	actionReadyDocumentPickup             = "action:ready_document:pickup"
	actionReadyDocumentEmail              = "action:ready_document:email"
	actionRegistrationOpen                = "action:registration:open"
	actionRegistrationRoleStudent         = "action:registration:role:student"
	actionRegistrationRoleStaff           = "action:registration:role:staff"

	sessionApplicationFilling = "application:filling"
	sessionReadyDocumentEmail = "ready_document:email"
	sessionRegistration       = "registration:filling"
)

type applicationActionMeta struct {
	role applicationRole
	doc  applicationType
}

var applicationActionPayloads = map[string]applicationActionMeta{
	actionApplicationStudentStudyCert: {
		role: roleStudent,
		doc:  applicationTypeStudyCertificate,
	},
	actionApplicationStudentAcademicLeave: {
		role: roleStudent,
		doc:  applicationTypeAcademicLeave,
	},
	actionApplicationStudentTransfer: {
		role: roleStudent,
		doc:  applicationTypeStudyTransfer,
	},
	actionApplicationTeacherWorkCert: {
		role: roleTeacher,
		doc:  applicationTypeWorkCertificate,
	},
}

const (
	startGreetingText = `Привет! 👋
Я — твой цифровой помощник в университете. 🎓✨

Я помогу:
→ 🧑‍🎓 Студентам: смотреть расписание, подавать заявки на справки и отпуска, отслеживать статусы и многое другое.
→ 👨‍🏫 Преподавателям и сотрудникам: управлять расписанием, согласовывать заявки и упростить документооборот.

Чтобы начать, нам нужно тебя узнать.
Все данные нужны, чтобы показывать только твоё расписание и давать доступ к личным документам. 🔒

Давай начнём? 🚀`
	readyDocumentNotificationText = `🎉 Ваша заявка готова!

✅ Статус: Обработана и готова к получению

Теперь вы можете:
• Забрать оригинал в деканате 📍
• Запросить отправку на вашу электронную почту 📧

Выберите удобный способ получения!`
	readyDocumentPickupText = `✅ Отлично! Ваша справка уже ждёт вас в деканате. 📄

📍 Не забудьте взять с собой студенческий билет или паспорт.

Часы работы деканата:
Пн-Пт: с 9:00 до 18:00
Обед: с 13:00 до 14:00

Желаем хорошего дня! 😊`
	readyDocumentEmailPromptText = `Хорошо! Чтобы отправить справку на email, пришлите нам, пожалуйста, вашу рабочую почту.
📧 Убедитесь, что почта корректна, чтобы письмо не потерялось.`
	readyDocumentEmailInvalidText = `Пожалуйста, укажите корректный рабочий email. Например: ivan.ivanov@university.ru`
	readyDocumentEmailSuccessText = `Отлично! Ваша справка с места работы была направлена на указанную электронную почту. 📨

Что делать дальше:

Проверьте входящие сообщения, а также папку «Спам», если письмо не пришло в течение 15 минут.

Если вы не получили письмо, пожалуйста, сообщите нам об этом.`
)

const (
	registrationIntroText = `Чтобы пользоваться сервисами университета, нужно один раз подтвердить свои данные.

Выберите роль, чтобы начать регистрацию:`
	registrationFullNamePromptText    = "Напишите ваше полное имя так, как в официальных документах."
	registrationUniversityPromptText  = "Выберите университет (ответьте номером из списка)."
	registrationFacultyPromptText     = "Выберите факультет (ответьте номером из списка)."
	registrationGroupPromptText       = "Выберите учебную группу (ответьте номером из списка)."
	registrationStudentCardPromptText = "Введите номер студенческого билета."
	registrationKafedraPromptText     = "Выберите кафедру (ответьте номером из списка)."
	registrationTabNumberPromptText   = "Введите табельный номер."
	registrationOptionsHintText       = "Отправьте номер подходящего варианта из списка."
	registrationCancelledText         = "Регистрация остановлена. В любой момент используйте /register, чтобы продолжить."
	registrationSuccessText           = "Готово! Вы успешно зарегистрированы. Теперь можно пользоваться всеми разделами бота."
	registrationRequiredText          = `Привет! 👋
Я — твой цифровой помощник в университете. 🎓✨

Я помогу:
→ 🧑‍🎓 Студентам: смотреть расписание, подавать заявки на справки и отпуска, отслеживать статусы и многое другое.
→ 👨‍🏫 Преподавателям и сотрудникам: управлять расписанием, согласовывать заявки и упростить документооборот.

Чтобы начать, нам нужно тебя узнать.
Все данные нужны, чтобы показывать только твоё расписание и давать доступ к личным документам. 🔒

Давай начнём? 🚀`
	registrationDataNotFoundText = `❌ Данные не найдены

Упс! Мы не смогли найти тебя в системе университета.

Возможные причины:
😢 Твои данные еще не внесли в цифровую систему вуза.
✍🏻 Опечатка в ФИО, номере группы, кафедры или табельного номера.

Что делать?
Обратись в деканат или отдел кадров твоего факультета, чтобы они добавили тебя в базу.`
)

var emailRegexp = regexp.MustCompile(`^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$`)

func registerDefaultBotHandlers(bot *appbot.Service, applications *applicationCoordinator, payments backend.Payments, schedule *scheduleService, registration *registrationCoordinator) {
	if bot == nil {
		panic("app: bot service is nil")
	}
	if applications == nil {
		panic("app: application coordinator is nil")
	}
	if payments == nil {
		panic("app: payment service is nil")
	}
	if schedule == nil {
		panic("app: schedule service is nil")
	}
	if registration == nil {
		panic("app: registration coordinator is nil")
	}
	menus := NewMenuRegistry(bot)
	registerMenus(menus)

	bot.RegisterBotStartedHandler(func(ctx context.Context, start *appbot.BotStartedContext) error {
		ok, err := ensureUserRegistered(ctx, start.Service(), applications, start.UserID(), start.ChatID())
		if err != nil {
			if err.Error() == "" {
				return nil
			}
			logger := start.Logger()
			logger.Error().Err(err).Msg("failed to ensure registration on bot start")
			return start.ReplyText(ctx, "Сервис временно недоступен, попробуйте позже.")
		}
		if !ok {
			return nil
		}
		if err := start.ReplyText(ctx, startGreetingText); err != nil && err.Error() != "" {
			logger := start.Logger()
			logger.Warn().Err(err).Msg("failed to send greeting on bot start")
		}
		if err := menus.Send(ctx, start.ChatID(), start.UserID(), menuRoot); err != nil && err.Error() != "" {
			logger := start.Logger()
			logger.Error().Err(err).Msg("failed to send menu on bot start")
			return start.ReplyText(ctx, "Главное меню временно недоступно. Отправьте /start чуть позже.")
		}
		return nil
	})

	bot.RegisterCommand(appbot.Command{
		Name:        "start",
		Description: "Показать главное меню",
		Handler: func(ctx context.Context, msg *appbot.MessageContext) error {
			ok, err := ensureUserRegistered(ctx, msg.Service(), applications, msg.SenderID(), msg.ChatID())
			if err != nil {
				if err.Error() == "" {
					return nil
				}
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to ensure registration on /start")
				return msg.ReplyText(ctx, "Сервис временно недоступен, попробуйте позже.")
			}
			if !ok {
				return nil
			}
			msg.ClearSessionState()
			if err := menus.Send(ctx, msg.ChatID(), msg.SenderID(), menuRoot); err != nil && err.Error() != "" {
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to send root menu")
				return msg.ReplyText(ctx, "Привет! Пока не могу показать меню, попробуйте позже.")
			}
			return nil
		},
	})

	bot.RegisterCommand(appbot.Command{
		Name:        "help",
		Description: "Показать список доступных команд",
		Handler: func(ctx context.Context, msg *appbot.MessageContext) error {
			ok, err := ensureUserRegistered(ctx, msg.Service(), applications, msg.SenderID(), msg.ChatID())
			if err != nil {
				if err.Error() == "" {
					return nil
				}
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to ensure registration on /help")
				return msg.ReplyText(ctx, "Сервис временно недоступен, попробуйте позже.")
			}
			if !ok {
				return nil
			}
			commands := bot.Commands()
			if len(commands) == 0 {
				return msg.ReplyText(ctx, "Команды ещё не подключены. Попробуйте позже.")
			}

			var b strings.Builder
			b.WriteString("Доступные команды:\n")
			for _, cmd := range commands {
				desc := cmd.Description
				if desc == "" {
					desc = "описание появится позже"
				}
				b.WriteString(fmt.Sprintf("/%s - %s\n", cmd.Name, desc))
			}
			b.WriteString("\nЧтобы открыть меню, введите /start или нажмите кнопку ниже.")

			return msg.ReplyText(ctx, b.String())
		},
	})

	bot.RegisterCommand(appbot.Command{
		Name:        "register",
		Description: "Подтвердить данные в университете",
		Handler: func(ctx context.Context, msg *appbot.MessageContext) error {
			msg.ClearSessionState()
			if err := sendRegistrationIntro(ctx, msg.Service(), msg.ChatID(), msg.SenderID(), ""); err != nil && err.Error() != "" {
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to start registration flow")
				return msg.ReplyText(ctx, "Не удалось отправить шаг регистрации. Попробуйте ещё раз позже.")
			}
			return nil
		},
	})

	bot.RegisterCallbackHandler(func(ctx context.Context, cb *appbot.CallbackContext) error {
		payload := cb.Payload()
		metaAction, hasApplicationAction := applicationActionPayloads[payload]
		requiresRegistration := payload != actionRegistrationOpen && payload != actionRegistrationRoleStudent && payload != actionRegistrationRoleStaff
		if requiresRegistration {
			ok, err := ensureUserRegistered(ctx, cb.Service(), applications, cb.SenderID(), cb.ChatID())
			if err != nil {
				if err.Error() == "" {
					return cb.Answer(ctx, nil)
				}
				logger := cb.Logger()
				logger.Error().Err(err).Msg("failed to ensure registration on callback")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Сервис временно недоступен, попробуйте позже."})
			}
			if !ok {
				return cb.Answer(ctx, nil)
			}
		}
		switch {
		case strings.HasPrefix(payload, "menu:"):
			if err := sendMenuFromCallback(ctx, menus, cb, payload); err != nil && err.Error() != "" {
				logger := cb.Logger()
				logger.Error().Err(err).Str("menu_id", payload).Msg("failed to send menu")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Меню временно недоступно"})
			}
			return nil

		case payload == actionRegistrationOpen:
			cb.ClearSessionState()
			if err := cb.Answer(ctx, nil); err != nil {
				return err
			}
			return sendRegistrationIntro(ctx, cb.Service(), cb.ChatID(), cb.SenderID(), "")

		case payload == actionRegistrationRoleStudent || payload == actionRegistrationRoleStaff:
			var role backend.UserRole
			switch payload {
			case actionRegistrationRoleStudent:
				role = backend.UserRoleStudent
			default:
				role = backend.UserRoleStaff
			}
			session := newRegistrationSession(role)
			payloadBytes, err := session.marshal()
			if err != nil {
				logger := cb.Logger()
				logger.Error().Err(err).Msg("failed to encode registration session")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось начать регистрацию, попробуйте позже"})
			}
			cb.SetSessionState(appbot.SessionState{
				Step:    sessionRegistration,
				Payload: payloadBytes,
			})
			if err := cb.Answer(ctx, nil); err != nil {
				return err
			}
			return sendRegistrationStepPrompt(ctx, cb.Service(), cb.ChatID(), cb.SenderID(), registrationFullNamePromptText, nil)

		case payload == actionApplicationsOpen:
			role, err := applications.ResolveRole(ctx, cb.SenderID())
			if err != nil {
				if errors.Is(err, backend.ErrUserNotFound) {
					if err := cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Нужна регистрация"}); err != nil {
						return err
					}
					if err := cb.ReplyText(ctx, registrationRequiredText); err != nil {
						return err
					}
					return sendRegistrationIntro(ctx, cb.Service(), cb.ChatID(), cb.SenderID(), "")
				}
				logger := cb.Logger()
				logger.Error().Err(err).Msg("failed to resolve user role")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "�?�� �?�?���>�?�?�? �?���?��?��>��'�? �?�?�?�'�?���?�<�� �����?�?���"})
			}

			var menuID string
			switch role {
			case roleStudent:
				menuID = menuApplicationsStudent
			case roleTeacher:
				menuID = menuApplicationsTeacher
			}
			if menuID == "" {
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось определить доступные заявки"})
			}
			if err := sendMenuFromCallback(ctx, menus, cb, menuID); err != nil && err.Error() != "" {
				logger := cb.Logger()
				logger.Error().Err(err).Str("menu_id", menuID).Msg("failed to send applications menu")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось открыть список заявок"})
			}
			return nil
		case hasApplicationAction:
			sessionData, err := applications.PrepareSession(cb.SenderID(), metaAction.role, metaAction.doc)
			if err != nil {
				logger := cb.Logger()
				logger.Error().Err(err).Str("doc_type", string(metaAction.doc)).Msg("failed to load application form")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось загрузить форму. Попробуйте позже"})
			}
			if sessionData.StepsCount() == 0 {
				if err := applications.Submit(ctx, cb.SenderID(), sessionData); err != nil {
					logger := cb.Logger()
					logger.Error().Err(err).Str("doc_type", string(metaAction.doc)).Msg("failed to submit auto form")
					return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось отправить заявку. Попробуйте позже"})
				}
				if err := cb.Answer(ctx, nil); err != nil {
					return err
				}
				if err := cb.ReplyText(ctx, formatSuccessMessage(sessionData.FormTitle)); err != nil {
					return err
				}
				return menus.Send(ctx, cb.ChatID(), cb.SenderID(), menuRoot)
			}
			payloadBytes, err := sessionData.marshal()
			if err != nil {
				logger := cb.Logger()
				logger.Error().Err(err).Str("doc_type", string(metaAction.doc)).Msg("failed to encode application session")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось подготовить форму. Попробуйте позже"})
			}
			cb.SetSessionState(appbot.SessionState{
				Step: sessionApplicationFilling,
				Params: map[string]string{
					"form_type": string(metaAction.doc),
					"role":      string(metaAction.role),
				},
				Payload: payloadBytes,
			})
			if err := cb.Answer(ctx, nil); err != nil {
				return err
			}
			return sendApplicationPrompt(ctx, cb.Service(), cb.ChatID(), cb.SenderID(), sessionData.StartPrompt())
		case payload == actionPaymentRequestOrder:
			status, err := payments.Status(ctx, cb.SenderID())
			if err != nil {
				logger := cb.Logger()
				logger.Error().Err(err).Msg("failed to fetch payment status")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось проверить оплату. Попробуйте позже"})
			}
			if !status.NeedDorm && !status.NeedTuition {
				if err := cb.Answer(ctx, nil); err != nil {
					return err
				}
				return cb.ReplyText(ctx, "Оплата не требуется — задолженностей нет.")
			}

			builder := cb.Service().NewKeyboardBuilder()
			if builder == nil {
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось построить меню оплат"})
			}

			row := builder.AddRow()
			if status.NeedDorm {
				row.AddCallback("💳 Оплатить общежитие", schemes.POSITIVE, actionPaymentDormPay)
			}
			if status.NeedTuition {
				if status.NeedDorm {
					row = builder.AddRow()
				}
				row.AddCallback("💳 Оплатить обучение", schemes.POSITIVE, actionPaymentTuitionPay)
			}

			backRow := builder.AddRow()
			backRow.AddCallback("Назад", schemes.DEFAULT, menuRoot)

			body := &schemes.NewMessageBody{
				Text: `Оплата услуг 🔒

Ваша безопасность — наш приоритет. Все платежи защищены.`,
			}
			body.Attachments = append(body.Attachments, schemes.NewInlineKeyboardAttachmentRequest(builder.Build()))

			if err := cb.Answer(ctx, &schemes.CallbackAnswer{Message: body}); err == nil {
				return nil
			} else {
				logger := cb.Logger()
				logger.Warn().Err(err).Msg("failed to update payments menu via callback answer, fallback to sending new one")
			}

			if err := cb.Answer(ctx, nil); err != nil {
				return err
			}

			msg := maxbot.NewMessage().SetText(body.Text)
			msg.SetUser(cb.SenderID())
			msg.SetChat(cb.ChatID())
			msg.AddKeyboard(builder)
			_, sendErr := cb.Service().SendMessage(ctx, msg)
			return sendErr
		case payload == actionPaymentDormPay:
			return sendPaymentLink(ctx, cb, payments, backend.PaymentKindDorm, "Оплатить общежитие можно по ссылке: %s")
		case payload == actionPaymentTuitionPay:
			return sendPaymentLink(ctx, cb, payments, backend.PaymentKindTuition, "Оплатить обучение можно по ссылке: %s")
		case payload == actionScheduleToday:
			text, err := schedule.Today(ctx, cb.SenderID())
			if err != nil {
				logger := cb.Logger()
				logger.Error().Err(err).Msg("failed to fetch schedule")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось получить расписание"})
			}
			if err := cb.Answer(ctx, nil); err != nil {
				return err
			}
			return cb.ReplyText(ctx, text)
		case payload == actionScheduleWeek:
			text, err := schedule.Week(ctx, cb.SenderID())
			if err != nil {
				logger := cb.Logger()
				logger.Error().Err(err).Msg("failed to fetch weekly schedule")
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось получить недельное расписание"})
			}
			if err := cb.Answer(ctx, nil); err != nil {
				return err
			}
			return cb.ReplyText(ctx, text)
		case payload == actionReadyDocumentPickup:
			if err := cb.Answer(ctx, nil); err != nil {
				return err
			}
			return cb.ReplyText(ctx, readyDocumentPickupText)
		case payload == actionReadyDocumentEmail:
			cb.SetSessionState(appbot.SessionState{
				Step: sessionReadyDocumentEmail,
			})
			if err := cb.Answer(ctx, nil); err != nil {
				return err
			}
			return cb.ReplyText(ctx, readyDocumentEmailPromptText)
		case payload == actionApplicationCancel:
			state, ok := cb.SessionState()
			if !ok || state.Step != sessionApplicationFilling {
				return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Нет заявки для отмены"})
			}
			cb.ClearSessionState()
			if err := cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Заполнение отменено"}); err != nil {
				return err
			}
			if err := cb.ReplyText(ctx, "Заполнение заявки остановлено. Можете начать заново через меню."); err != nil {
				return err
			}
			return menus.Send(ctx, cb.ChatID(), cb.SenderID(), menuRoot)
		default:
			return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Неизвестное действие"})
		}
	})

	bot.RegisterSessionHandler(sessionApplicationFilling, func(ctx context.Context, msg *appbot.MessageContext, state appbot.SessionState) error {
		progress, err := applicationSessionFromPayload(state.Payload)
		if err != nil {
			logger := msg.Logger()
			logger.Error().Err(err).Msg("failed to restore application session")
			msg.ClearSessionState()
			return msg.ReplyText(ctx, "Не удалось восстановить заявку. Пожалуйста, начните оформление заново через меню.")
		}

		field, ok := progress.currentField()
		if !ok {
			msg.ClearSessionState()
			return msg.ReplyText(ctx, "Заявка уже заполнена. Откройте меню и создайте новую, если нужно.")
		}

		switch field.Kind {
		case fieldKindFile:
			raw := msg.Update().Message.Body.RawAttachments
			if len(raw) == 0 {
				return msg.ReplyText(ctx, "Пожалуйста, прикрепите нужный файл к сообщению и отправьте его ещё раз.")
			}
			payload, err := encodeAttachments(raw)
			if err != nil {
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to encode attachments")
				return msg.ReplyText(ctx, "Не удалось обработать файл. Отправьте его ещё раз.")
			}
			progress.RecordFileAnswer(payload)
		default:
			answer := strings.TrimSpace(msg.Text())
			if field.Required && answer == "" {
				return msg.ReplyText(ctx, progress.ReminderForRequiredField())
			}
			progress.RecordAnswer(answer)
		}

		if progress.IsCompleted() {
			if err := applications.Submit(ctx, msg.SenderID(), progress); err != nil {
				if errors.Is(err, backend.ErrUserNotFound) {
					msg.ClearSessionState()
					if err := msg.ReplyText(ctx, registrationRequiredText); err != nil {
						return err
					}
					return sendRegistrationIntro(ctx, msg.Service(), msg.ChatID(), msg.SenderID(), "")
				}
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to submit application")
				msg.ClearSessionState()
				return msg.ReplyText(ctx, "�?�� �?�?���>�?�?�? �?�'���?���?��'�? �����?�?��?. �?�?���?�?�+�?���'�� ���?�?�'�?�?��'�? �ؑ?�'�? ���?������")
			}

			msg.ClearSessionState()
			if err := msg.ReplyText(ctx, formatSuccessMessage(progress.FormTitle)); err != nil {
				return err
			}
			if err := menus.Send(ctx, msg.ChatID(), msg.SenderID(), menuRoot); err != nil && err.Error() != "" {
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to send menu after application submission")
				return msg.ReplyText(ctx, "Главное меню сейчас недоступно. Вызовите /start позднее.")
			}
			return nil
		}

		payloadBytes, err := progress.marshal()
		if err != nil {
			logger := msg.Logger()
			logger.Error().Err(err).Msg("failed to encode application session")
			msg.ClearSessionState()
			return msg.ReplyText(ctx, "Не удалось сохранить ответ. Перезапустите оформление заявки.")
		}

		newParams := map[string]string{}
		for k, v := range state.Params {
			newParams[k] = v
		}

		msg.SetSessionState(appbot.SessionState{
			Step:    sessionApplicationFilling,
			Params:  newParams,
			Payload: payloadBytes,
		})

		return sendApplicationPrompt(ctx, msg.Service(), msg.ChatID(), msg.SenderID(), progress.NextPrompt())
	})

	bot.RegisterSessionHandler(sessionRegistration, func(ctx context.Context, msg *appbot.MessageContext, state appbot.SessionState) error {
		data, err := registrationSessionFromPayload(state.Payload)
		if err != nil {
			logger := msg.Logger()
			logger.Error().Err(err).Msg("failed to restore registration session")
			msg.ClearSessionState()
			return msg.ReplyText(ctx, "Не удалось восстановить регистрацию. Отправьте /register, чтобы начать заново.")
		}

		answer := strings.TrimSpace(msg.Text())
		lower := strings.ToLower(answer)
		if lower == "отмена" || lower == "/cancel" {
			msg.ClearSessionState()
			return msg.ReplyText(ctx, registrationCancelledText)
		}

		var nextPrompt string
		var options []registrationOption

		switch data.Step {
		case registrationStepFullName:
			if answer == "" {
				return msg.ReplyText(ctx, registrationFullNamePromptText)
			}
			data.FullName = answer
			data.Step = registrationStepUniversity
			if err := registration.LoadOptions(ctx, &data); err != nil {
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to load universities")
				msg.ClearSessionState()
				return msg.ReplyText(ctx, err.Error())
			}
			options = data.Options
			nextPrompt = registrationUniversityPromptText
		case registrationStepUniversity:
			opt, selErr := data.selectOption(answer)
			if selErr != nil {
				return msg.ReplyText(ctx, registrationOptionsHintText)
			}
			data.University = registrationUniversity{ID: opt.ID, Name: opt.Title, City: opt.Subtitle}
			data.Step = registrationStepFaculty
			if err := registration.LoadOptions(ctx, &data); err != nil {
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to load faculties")
				msg.ClearSessionState()
				return msg.ReplyText(ctx, err.Error())
			}
			options = data.Options
			nextPrompt = registrationFacultyPromptText
		case registrationStepFaculty:
			opt, selErr := data.selectOption(answer)
			if selErr != nil {
				return msg.ReplyText(ctx, registrationOptionsHintText)
			}
			data.Faculty = registrationEntity{ID: opt.ID, Title: opt.Title}
			if data.Role == backend.UserRoleStudent {
				data.Step = registrationStepGroup
				if err := registration.LoadOptions(ctx, &data); err != nil {
					logger := msg.Logger()
					logger.Error().Err(err).Msg("failed to load groups")
					msg.ClearSessionState()
					return msg.ReplyText(ctx, err.Error())
				}
				options = data.Options
				nextPrompt = registrationGroupPromptText
			} else {
				data.Step = registrationStepKafedra
				if err := registration.LoadOptions(ctx, &data); err != nil {
					logger := msg.Logger()
					logger.Error().Err(err).Msg("failed to load kafedras")
					msg.ClearSessionState()
					return msg.ReplyText(ctx, err.Error())
				}
				options = data.Options
				nextPrompt = registrationKafedraPromptText
			}
		case registrationStepGroup:
			opt, selErr := data.selectOption(answer)
			if selErr != nil {
				return msg.ReplyText(ctx, registrationOptionsHintText)
			}
			data.Group = registrationGroup{ID: opt.ID, Name: opt.Title, Code: opt.Subtitle}
			data.Step = registrationStepStudentCard
			data.clearOptions()
			nextPrompt = registrationStudentCardPromptText
		case registrationStepStudentCard:
			if answer == "" {
				return msg.ReplyText(ctx, registrationStudentCardPromptText)
			}
			data.StudentCard = answer
			return completeRegistration(ctx, msg, menus, registration, data)
		case registrationStepKafedra:
			opt, selErr := data.selectOption(answer)
			if selErr != nil {
				return msg.ReplyText(ctx, registrationOptionsHintText)
			}
			data.Kafedra = registrationEntity{ID: opt.ID, Title: opt.Title}
			data.Step = registrationStepTabNumber
			data.clearOptions()
			nextPrompt = registrationTabNumberPromptText
		case registrationStepTabNumber:
			if answer == "" {
				return msg.ReplyText(ctx, registrationTabNumberPromptText)
			}
			data.TabNumber = answer
			return completeRegistration(ctx, msg, menus, registration, data)
		default:
			msg.ClearSessionState()
			return msg.ReplyText(ctx, "Неизвестный шаг регистрации. Отправьте /register, чтобы начать заново.")
		}

		payloadBytes, err := data.marshal()
		if err != nil {
			logger := msg.Logger()
			logger.Error().Err(err).Msg("failed to encode registration session")
			msg.ClearSessionState()
			return msg.ReplyText(ctx, "Не удалось сохранить прогресс регистрации. Отправьте /register, чтобы начать заново.")
		}

		msg.SetSessionState(appbot.SessionState{
			Step:    sessionRegistration,
			Payload: payloadBytes,
		})

		return sendRegistrationStepPrompt(ctx, msg.Service(), msg.ChatID(), msg.SenderID(), nextPrompt, options)
	})

	bot.RegisterSessionHandler(sessionReadyDocumentEmail, func(ctx context.Context, msg *appbot.MessageContext, state appbot.SessionState) error {
		email := strings.TrimSpace(msg.Text())
		if email == "" {
			return msg.ReplyText(ctx, readyDocumentEmailPromptText)
		}
		if !emailRegexp.MatchString(email) {
			return msg.ReplyText(ctx, readyDocumentEmailInvalidText)
		}

		msg.ClearSessionState()
		if err := msg.ReplyText(ctx, readyDocumentEmailSuccessText); err != nil {
			return err
		}
		return nil
	})

	bot.RegisterMessageHandler(func(ctx context.Context, msg *appbot.MessageContext) error {
		ok, err := ensureUserRegistered(ctx, msg.Service(), applications, msg.SenderID(), msg.ChatID())
		if err != nil {
			if err.Error() == "" {
				return nil
			}
			logger := msg.Logger()
			logger.Error().Err(err).Msg("failed to ensure registration on text message")
			return msg.ReplyText(ctx, "Сервис временно недоступен, попробуйте позже.")
		}
		if !ok {
			return nil
		}
		text := strings.TrimSpace(msg.Text())
		if text == "" {
			return nil
		}
		switch strings.ToLower(text) {
		case "hi", "привет":
			return msg.ReplyText(ctx, "Привет! Жмите кнопки меню или команду /start.")
		case "меню":
			if err := menus.Send(ctx, msg.ChatID(), msg.SenderID(), menuRoot); err != nil && err.Error() != "" {
				logger := msg.Logger()
				logger.Error().Err(err).Msg("failed to send menu from text shortcut")
				return msg.ReplyText(ctx, "Не смог показать меню. Попробуйте /start чуть позже.")
			}
			return nil
		}

		if msg.Command() != "" {
			return msg.ReplyText(ctx, "Неизвестная команда. Введите /help, чтобы узнать, что уже работает.")
		}

		return msg.ReplyText(ctx, "Используйте меню или /help, чтобы посмотреть доступные действия.")
	})
}

func registerMenus(menus *MenuRegistry) {
	menus.Register(Menu{
		ID: menuRoot,
		Title: `Добро пожаловать в главное меню! 🎓

Выберите, что вас интересует:

1. Платежи 💳 — Проверить баланс и оплатить обучение или общежитие.
2. Расписание 📚 — Посмотреть ваше расписание на текущую неделю.
3. Заявления 📄 — Подать заявку на справку, академический отпуск или перевод.

Просто нажмите на одну из кнопок ниже, чтобы продолжить! 👇`,
		Rows: [][]MenuButton{
			{
				{Text: "Платежи", Payload: actionPaymentRequestOrder, Intent: schemes.POSITIVE},
				{Text: "Расписание", Payload: menuSchedule, Intent: schemes.DEFAULT},
			},
			{
				{Text: "Заявления", Payload: actionApplicationsOpen, Intent: schemes.POSITIVE},
			},
		},
	})

	menus.Register(Menu{
		ID: menuSchedule,
		Title: `📅 Какое расписание вас интересует?

Выберите вариант ниже, чтобы посмотреть`,
		Rows: [][]MenuButton{
			{
				{Text: "Сегодня", Payload: actionScheduleToday, Intent: schemes.DEFAULT},
			},
			{
				{Text: "Назад", Payload: menuRoot, Intent: schemes.DEFAULT},
			},
		},
	})

	menus.Register(Menu{
		ID:    menuApplicationsStudent,
		Title: "📄 Выберите тип заявления, которое хотите подать:",
		Rows: [][]MenuButton{
			{
				{Text: "Справка с места обучения 🎓", Payload: actionApplicationStudentStudyCert, Intent: schemes.POSITIVE},
			},
			{
				{Text: "Справка об уходе в академ 📅", Payload: actionApplicationStudentAcademicLeave, Intent: schemes.POSITIVE},
			},
			{
				{Text: "Перевод на другую программу", Payload: actionApplicationStudentTransfer, Intent: schemes.POSITIVE},
			},
			{
				{Text: "Назад", Payload: menuRoot, Intent: schemes.DEFAULT},
			},
		},
	})

	menus.Register(Menu{
		ID:    menuApplicationsTeacher,
		Title: "Заявления преподавателей:",
		Rows: [][]MenuButton{
			{
				{Text: "Справка с места работы", Payload: actionApplicationTeacherWorkCert, Intent: schemes.POSITIVE},
			},
			{
				{Text: "Назад", Payload: menuRoot, Intent: schemes.DEFAULT},
			},
		},
	})
}

func sendMenuFromCallback(ctx context.Context, menus *MenuRegistry, cb *appbot.CallbackContext, menuID string) error {
	body, err := menus.buildMenuBody(menuID)
	if err != nil {
		return err
	}
	answer := &schemes.CallbackAnswer{Message: body}
	if err := cb.Answer(ctx, answer); err != nil {
		logger := cb.Logger()
		logger.Warn().
			Err(err).
			Str("menu_id", menuID).
			Msg("failed to update menu via callback answer, fallback to sending new one")
		return menus.Send(ctx, cb.ChatID(), cb.SenderID(), menuID)
	}
	return nil
}

func sendApplicationPrompt(ctx context.Context, svc *appbot.Service, chatID, userID int64, text string) error {
	if svc == nil {
		return fmt.Errorf("application prompt sender is nil")
	}

	msg := maxbot.NewMessage().SetText(text)
	if userID != 0 {
		msg.SetUser(userID)
	}
	if chatID != 0 {
		msg.SetChat(chatID)
	}

	if builder := svc.NewKeyboardBuilder(); builder != nil {
		builder.AddRow().AddCallback("Отменить заполнение", schemes.NEGATIVE, actionApplicationCancel)
		msg.AddKeyboard(builder)
	}

	_, err := svc.SendMessage(ctx, msg)
	return err
}

func sendReadyNotification(ctx context.Context, svc *appbot.Service, userID int64) error {
	if svc == nil {
		return fmt.Errorf("ready notification sender is nil")
	}
	if userID <= 0 {
		return fmt.Errorf("ready notification user id must be positive")
	}

	msg := maxbot.NewMessage().SetText(readyDocumentNotificationText)
	msg.SetUser(userID)

	builder := svc.NewKeyboardBuilder()
	if builder == nil {
		return fmt.Errorf("ready notification keyboard builder is nil")
	}
	row := builder.AddRow()
	row.AddCallback("Забрать в деканате", schemes.POSITIVE, actionReadyDocumentPickup)
	row.AddCallback("Отправить на почту", schemes.DEFAULT, actionReadyDocumentEmail)
	msg.AddKeyboard(builder)

	_, err := svc.SendMessage(ctx, msg)
	return err
}

func ensureUserRegistered(ctx context.Context, svc *appbot.Service, applications *applicationCoordinator, userID, chatID int64) (bool, error) {
	if applications == nil {
		return true, nil
	}

	_, err := applications.ResolveRole(ctx, userID)
	if err == nil {
		return true, nil
	}
	if errors.Is(err, backend.ErrUserNotFound) {
		if err := sendRegistrationIntro(ctx, svc, chatID, userID, registrationRequiredText); err != nil {
			return false, err
		}
		return false, nil
	}
	return false, err
}

func sendRegistrationIntro(ctx context.Context, svc *appbot.Service, chatID, userID int64, notice string) error {
	if svc == nil {
		return fmt.Errorf("registration intro sender is nil")
	}

	text := registrationIntroText
	if extra := strings.TrimSpace(notice); extra != "" {
		text = fmt.Sprintf("%s\n\n%s", extra, registrationIntroText)
	}

	msg := maxbot.NewMessage().SetText(text)
	if userID != 0 {
		msg.SetUser(userID)
	}
	if chatID != 0 {
		msg.SetChat(chatID)
	}

	builder := svc.NewKeyboardBuilder()
	if builder == nil {
		return fmt.Errorf("registration keyboard builder is nil")
	}

	row := builder.AddRow()
	row.AddCallback("Я студент", schemes.POSITIVE, actionRegistrationRoleStudent)
	row.AddCallback("Я преподаватель/сотрудник", schemes.DEFAULT, actionRegistrationRoleStaff)
	msg.AddKeyboard(builder)

	_, err := svc.SendMessage(ctx, msg)
	return err
}

func sendRegistrationStepPrompt(ctx context.Context, svc *appbot.Service, chatID, userID int64, prompt string, options []registrationOption) error {
	if svc == nil {
		return fmt.Errorf("registration prompt sender is nil")
	}

	text := prompt
	if list := formatRegistrationOptions(options); list != "" {
		text = fmt.Sprintf("%s\n\n%s\n\n%s", prompt, list, registrationOptionsHintText)
	}

	msg := maxbot.NewMessage().SetText(text)
	if userID != 0 {
		msg.SetUser(userID)
	}
	if chatID != 0 {
		msg.SetChat(chatID)
	}

	_, err := svc.SendMessage(ctx, msg)
	return err
}

func completeRegistration(ctx context.Context, msg *appbot.MessageContext, menus *MenuRegistry, registration *registrationCoordinator, data registrationSessionData) error {
	if registration == nil {
		return fmt.Errorf("registration service is not configured")
	}

	result, err := registration.Register(ctx, msg.SenderID(), data)
	if err != nil {
		logger := msg.Logger()
		var httpErr *backend.HTTPError
		if errors.As(err, &httpErr) {
			status := httpErr.StatusCode
			if (status == http.StatusBadRequest || status == http.StatusNotFound) && strings.Contains(strings.ToLower(httpErr.Body), "не найд") {
				logger.Info().Err(err).Msg("registration data mismatch")
				msg.ClearSessionState()
				return msg.ReplyText(ctx, registrationDataNotFoundText)
			}
		}
		logger.Error().Err(err).Msg("registration failed")
		msg.ClearSessionState()
		return msg.ReplyText(ctx, fmt.Sprintf("Не удалось завершить регистрацию: %v", err))
	}

	msg.ClearSessionState()
	successText := registrationSuccessText
	if extra := strings.TrimSpace(result.Message); extra != "" {
		successText = fmt.Sprintf("%s\n\n%s", registrationSuccessText, extra)
	}
	if err := msg.ReplyText(ctx, successText); err != nil {
		return err
	}

	if menus != nil {
		if err := menus.Send(ctx, msg.ChatID(), msg.SenderID(), menuRoot); err != nil && err.Error() != "" {
			logger := msg.Logger()
			logger.Warn().Err(err).Msg("failed to send menu after registration")
		}
	}
	return nil
}

// encodeAttachments приводит список вложений к JSON-строке,
// чтобы backend смог восстановить исходные файлы.
func encodeAttachments(raw []json.RawMessage) (string, error) {
	data, err := json.Marshal(raw)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// sendPaymentLink запрашивает ссылку на оплату и отправляет её пользователю.
func sendPaymentLink(ctx context.Context, cb *appbot.CallbackContext, payments backend.Payments, kind backend.PaymentKind, template string) error {
	link, err := payments.Link(ctx, cb.SenderID(), kind)
	if err != nil {
		logger := cb.Logger()
		logger.Error().Err(err).Str("payment_kind", string(kind)).Msg("failed to create payment link")
		return cb.Answer(ctx, &schemes.CallbackAnswer{Notification: "Не удалось сформировать ссылку на оплату"})
	}
	if err := cb.Answer(ctx, nil); err != nil {
		return err
	}
	return cb.ReplyText(ctx, fmt.Sprintf(template, link))
}
