# DeployBot Swarm

A modular **Streamlit** app scaffold for experimenting with a swarm of agents backed by pluggable LLM providers.

## Project layout

- `app.py`: Streamlit entrypoint
- `agents/`: agent implementations
- `llm/`: LLM engines + routing
- `utils/`: shared utilities (config, logging, helpers)
- `data/`: local data files (kept out of source control if needed)

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Optionally create a `.env` file in the project root (example keys you may use):

```bash
GOOGLE_API_KEY=your_key_here
```

## Run

```bash
streamlit run app.py
```

