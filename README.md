# SupportPilot – Module 1: Ticket Processing & Classification

Employees sign up, raise tickets and see their ID and expected resolution time. The AI classifies each ticket
(category, sub-category, severity, priority). The admin sees every ticket with its classification and can close or reopen it.
Everything is password protected and stored in MySQL.

## Configuration

Set `ADMIN_PASSWORD` and `SECRET_KEY` in the environment before starting the app. Configure the database with
`DATABASE_URL`, or use `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`. The default database
host is `127.0.0.1`; set a non-empty database password when required. Do not commit credentials or local ticket data.
