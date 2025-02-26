# A desktop crossplatform app: Tauri + Python + React with Typescript App to perform semantic search on top of your FS

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

#### Download models for 100% local app
```bash
source infra/dev-scripts/download_models.sh
```
Will download the models in the `models` folder removing all previous models in the folder.
