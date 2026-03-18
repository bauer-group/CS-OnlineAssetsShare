## [1.0.3](https://github.com/bauer-group/CS-OnlineAssetsShare/compare/v1.0.2...v1.0.3) (2026-03-18)

### 🐛 Bug Fixes

* **minio:** corrected region format from AWS to MinIO standard ([635f6eb](https://github.com/bauer-group/CS-OnlineAssetsShare/commit/635f6eb94a4cf6c0e5cbdcf88409109497080baa))

## [1.0.2](https://github.com/bauer-group/CS-OnlineAssetsShare/compare/v1.0.1...v1.0.2) (2026-03-18)

### 🐛 Bug Fixes

* **config:** corrected region format in configuration ([608f9aa](https://github.com/bauer-group/CS-OnlineAssetsShare/commit/608f9aa71282f5d6c353cbfea77daa8ce0e3f922))

## [1.0.1](https://github.com/bauer-group/IP-OnlineAssetsShare/compare/v1.0.0...v1.0.1) (2026-03-16)

### 🐛 Bug Fixes

* **docker-compose:** removed MinIO console credentials ([3aa565a](https://github.com/bauer-group/IP-OnlineAssetsShare/commit/3aa565a7e3ecd03e2cd73f1683a348a6394f9833))

## [1.0.0](https://github.com/bauer-group/IP-OnlineAssetsShare/compare/v0.3.1...v1.0.0) (2026-03-16)

### ⚠ BREAKING CHANGES

* **compose:** Host-side mount point changed from ./config (directory)
to ./config/init.json (single file). Deployments relying on additional
files under ./config being available inside the container must update
their volume configuration accordingly.

### ♻️ Refactoring

* **compose:** simplified MinIO config mount to single file ([2effd16](https://github.com/bauer-group/IP-OnlineAssetsShare/commit/2effd1675110c6660a6ec39f716a596450e8c707))

## [0.3.1](https://github.com/bauer-group/IP-OnlineAssetsShare/compare/v0.3.0...v0.3.1) (2026-03-16)

### ♻️ Refactoring

* **docker:** mounted full config dir and added MINIO_INIT_CONFIG env ([e9811d6](https://github.com/bauer-group/IP-OnlineAssetsShare/commit/e9811d6b6ee38e6c90320c6e76dfbfe4d028d1c0))

## [0.3.0](https://github.com/bauer-group/IP-OnlineAssetsShare/compare/v0.2.0...v0.3.0) (2026-03-16)

### 🚀 Features

* init.json merge and validation CI/CD ([116fbbe](https://github.com/bauer-group/IP-OnlineAssetsShare/commit/116fbbed6290c61ff87313661d001cf34fa2612b))

## [0.2.0](https://github.com/bauer-group/IP-OnlineAssetsShare/compare/v0.1.0...v0.2.0) (2026-03-16)

### 🚀 Features

* **infra:** added OnlineAssetsShare initial project scaffold ([8b9049b](https://github.com/bauer-group/IP-OnlineAssetsShare/commit/8b9049b3eeaa013aedcba064e709d38e56f08abf))

## [0.1.0](https://github.com/bauer-group/IP-OnlineAssetsShare/compare/v0.0.0...v0.1.0) (2026-03-16)

### 🚀 Features

* Environment Setup ([8f8d261](https://github.com/bauer-group/IP-OnlineAssetsShare/commit/8f8d2616dee31cc852f65cd02e7c1eef46a594a4))
