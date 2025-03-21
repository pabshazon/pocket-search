cd ${POCKET_GITHUB_PATH}client/desktop-app/rust-tauri
export LIBSQLITE3_SYS_USE_PKG_CONFIG=0
export SQLITE3_CFLAGS="-DSQLITE_ENABLE_LOAD_EXTENSION=1"
cargo clean
cargo build
