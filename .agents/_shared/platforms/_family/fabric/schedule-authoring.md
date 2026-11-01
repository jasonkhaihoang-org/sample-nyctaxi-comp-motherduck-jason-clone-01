# Fabric Schedule Authoring

Author a DataPipeline's `.schedules` file in Fabric's `gitIntegration/schedules/1.0.0` schema. Every committed entry has `"enabled": false`; activation belongs to deployment, and a runner notebook never carries this file.

## Field Rules

- Set `jobType` to `"Execute"` for a DataPipeline. `Pipeline` is the scheduler API's path segment, not this field's value.
- Set `configuration.type` to `Cron` with `interval` in minutes, `Daily` or `Weekly` with `times` as `HH:MM` and `weekdays` for Weekly, or `Monthly` with `times`, numeric month-interval `recurrence`, and `occurrence`.
- For Monthly, set `occurrence` to `{occurrenceType: "DayOfMonth", dayOfMonth: 1-31}` or `{occurrenceType: "OrdinalWeekday", weekIndex: First|Second|Third|Fourth|Fifth, weekday: <day>}`. Microsoft's published schema spells the last key `WeekDay`, but Fabric's own output uses `weekday`; author Fabric's spelling.
- Set `localTimeZoneId` to the Windows time-zone id of the zone the schedule's times are in: `Eastern Standard Time` for New York (it follows daylight saving), `UTC` only when the times are UTC. An IANA name such as `America/New_York` is not a Fabric zone.
- Write `startDateTime` and `endDateTime` either with an offset such as `2026-08-04T06:30:00.000Z` or without one such as `2026-08-04T06:30:00`. Fabric accepts both and normalizes to the offset-free form, so prefer that form.
