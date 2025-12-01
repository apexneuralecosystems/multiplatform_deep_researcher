# Multiplatform Deep Researcher

We're building an MCP-powered multi-agent, multi-platform deep researcher. It performs deep web searches using [Bright Data's Web MCP server](https://brightdata.com/ai/mcp-server), with agents orchestrated through [CrewAI](https://docs.crewai.com/).

## Features

- **Multi-Platform Research**: Scrapes and analyzes content from Instagram, LinkedIn, YouTube, X (Twitter), and the open web.
- **Parallel Processing**: Uses asynchronous agents to research multiple platforms simultaneously.
- **MCP Integration**: Leverages the Model Context Protocol (MCP) to interact with Bright Data's scraping tools.
- **Interactive UI**: Built with Streamlit for an easy-to-use interface.

## Prerequisites

- Python 3.10+
- Node.js & npm (for the MCP server)
- [uv](https://github.com/astral-sh/uv) (recommended for Python dependency management)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd multiplatform_deep_researcher
    ```

2.  **Install Python dependencies:**
    ```bash
    uv sync
    # Or with pip:
    # pip install -r requirements.txt
    ```

3.  **Install Node.js dependencies:**
    This project requires the `@brightdata/mcp` package to be installed locally.
    ```bash
    npm install
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory:
    ```env
    OPENROUTER_API_KEY=sk-or-v1-...
    BRIGHT_DATA_API_TOKEN=<your_bright_data_api_token>
    ```

## Running the Application

1.  **Activate the virtual environment:**
    ```bash
    # Windows
    .venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    ```

2.  **Start the Streamlit App:**
    ```bash
    streamlit run app.py
    ```

3.  **Access the UI:**
    Open your browser and go to `http://localhost:8501`.

## Troubleshooting

- **Application Hangs on "Researching..."**: Ensure you have a stable internet connection. The first run might take a moment to initialize the Bright Data MCP server zones.
- **MCP Server Issues**: The application tries to run the MCP server using `node` directly from `node_modules`. Ensure `npm install` was successful.
