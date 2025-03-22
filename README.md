# A desktop crossplatform app to perform semantic search on top of your FS

### Development

### Install Dependencies
```
brew update
brew install sqlite
```

#### Run the app locally
```bash
infra/dev-scripts/run_local.sh
infra/dev-scripts/run_local.sh clean # to clean cargo and build from zero.
```

#### Refresh the local database
```bash
infra/dev-scripts/refresh_local.sh
```
Will remove the local database file.

#### Download models for 100% local app
```bash
infra/dev-scripts/download_models.sh
```
Will download the models in the `models` folder removing all previous models in the folder.
