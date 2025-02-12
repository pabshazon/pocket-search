# Tauri + Python + React with Typescript
Goal: to organize all my documents with reasoning added synth data and metadata.

# Functional requirements
1. Find all PDFs files in a Specific folder and subfolders -r (of a few high priority file types .key, .docx, .xlsx, .csv, .ppt)
2. Expand search and analysis capabilities with vectors and llm pre-processing for all PDFs selected (mvp - pdf is a photocopy vs digital native, and added metadata summaries of chapters and sections).
3. Act as a middleware for other apps, listening to the selected files and folders via FSEvents and other mechanisms, to sync cdc in real time local files with a local reasoning model that can use tools for future RAG - struct data, vector embeddings strategies, knowledge graphs, and ontologies technologies.


### Development

#### Run the app locally
```bash
source infra/dev-scripts/run_local.sh
```

#### Refresh the local database
```bash
source infra/dev-scripts/refresh_local.sh
```
Will remove the local database file.

