# Meeting Notes AI

A small web application that urns meeting transcripts into structured notes. The users can paste or upload their meeting transcripts and the AI model produces a summary, list of decisions, and action items with owners and due dates where the transcript states them.

Every AI result is treated as untrusted input: it is validated against a schema before svaing, and users can edit everything the AI produces. Nothing is inveted. If the transcript doesn't name an owner or date, the field is left blank for review.

## Planned Features

- Register, log in and delete your account (soft delete)
- Upload or paste transcripts, stored with title, date and original text
- AI analysis: summary, decisions, action items (what, owner, due date)
- Edit any AI output: add, delete and tick off action items (to do, in progress, done)
- Meeting list and detail pages
"My open action items" view across meetings, filterable by status, owner, and overdue.

## Status
Early planning. Nothing is built yet.

## Setup
Instructions will be added once the project runs locally

## Key decisions
To be documented as they're made, including the stack, session method, and how AI tools are used.
