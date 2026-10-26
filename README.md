# PR Lead Scraper Dashboard

*Finds people looking to hire a PR agency and puts them on a dashboard you can act on.*

It searches Bluesky and Hacker News for posts from people looking for a PR agency or publicist, keeps each lead once, and gives you one-click links to the original post and an email button.

Status: in progress.

## What it will do

- Search Bluesky and Hacker News for phrases like "looking for a PR agency" and "hiring publicist". The phrases live in one config file, so adding a new one doesn't need any code.
- Save each lead once: name, bio, company when the profile shows it, a preview of the post, a link, the platform and the time.
- Look up a work email with Hunter.io when you ask for it.
- Show every lead as a card with "View post" and "Email" buttons, plus filters and a CSV download.
- Run the search again every few hours on its own.

## Built with

Python, requests, SQLite, Streamlit, pandas and the Hunter.io API.

## Project structure

```
scraper/
├── keywords.yaml    the phrases to search, plus settings for each source
└── bluesky.py       searches Bluesky posts and turns matches into leads
```

## Setup

A step-by-step setup guide for non-technical users, with screenshots and a one-click Streamlit Cloud deploy, will be added with the first working version.
