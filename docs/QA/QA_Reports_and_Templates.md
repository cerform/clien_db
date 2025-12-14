# QA Reports and Templates

## Bug Report Template
- Title
- Description
- Steps to Reproduce
- Expected Result
- Actual Result
- Severity/Priority
- Environment
- Attachments / Logs
- Suggested Fix / Notes

## Test Readiness Report (TRR)
- Summary of environment
- Configs loaded
- Test coverage readiness
- Blockers

## QA Completion Report (QCR)
- Summary of tests executed
- Bugs found (by severity)
- Outstanding risks
- Release recommendation

## Example Bug Report (1)
- Title: Bot ignores new booking command from admin
- Description: Admin sends /booking command, bot responds with menu but no booking created
- Steps: (1) Login as admin, (2) /booking, (3) select service
- Expected: Booking created & sheet updated
- Actual: UI shows menu but no backend row created
- Severity: High
- Environment: Cloud Run dev
- Logs: [link to logs]

*** End of File
