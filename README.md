# Hevy Streamlit Dashboard

A small personal dashboard that uses the [Hevy public API](https://api.hevyapp.com/docs/) to
show your workout data in a mobile‑friendly Streamlit app.

> **Important:** Never hard‑code your Hevy API key in code or commit it to Git. Use
> a `.env` file or environment variable instead.

---

## 1. Setup

From `c:\Users\croger\Documents\Perso`:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Make sure you have a Hevy Pro subscription and generate an API key from:

- `https://hevy.com/settings?developer`

Create a file named `.env` in this folder with:

```text
HEVY_API_KEY=YOUR_HEVY_API_KEY_HERE
```

Alternatively, you can set `HEVY_API_KEY` as an environment variable in the shell where
you will run Streamlit.

---

## 2. Run the dashboard

```bash
streamlit run app.py
```

By default, Streamlit prints a local URL (like `http://localhost:8501`) and a network URL
(something like `http://192.168.x.x:8501`).

- On your **PC**, open the local URL.
- On your **phone (same Wi‑Fi)**, open the **network URL** in a mobile browser to see the
  dashboard.

---

## 3. What the app shows

- Basic user profile info from `GET /v1/user/info`
- Recent workouts from `GET /v1/workouts` (first page)
- A compact table of recent workouts
- A simple training volume chart (if the API exposes a volume field)
- Raw JSON responses inside an expander for debugging / exploring the schema

You can extend the app by:

- Adding more endpoints from the docs (routines, exercise templates, exercise history)
- Building custom charts and stats for key lifts
- Styling the layout specifically for your phone usage

