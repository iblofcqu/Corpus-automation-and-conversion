# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [1.3.0](https://github.com/iblofcqu/Corpus-automation-and-conversion/compare/v1.2.0...v1.3.0) (2026-01-25)


### Features

* 强制OCR 模式 ([721242c](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/721242c4e589bac1c611f3d84d3a182f3ae4b1cf))

## [1.2.0](https://github.com/iblofcqu/Corpus-automation-and-conversion/compare/v1.2.0-dev.0...v1.2.0) (2026-01-25)


### Features

* 创建项目增加描述 ([45c575d](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/45c575d07c036758fe5d4ab23076f92ba2c700f5))
* 文件删除API ([1546826](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/1546826898343514ea52942e2bea3fe497ab8240))
* 文件上传接口增加文件大小记录 ([51099d5](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/51099d556624d496d75dcb9f6e1fdd36acf6049c))
* 文件上传接口增加文件名传入 ([71606d4](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/71606d4fea9707d26aa9e401d800e055e08351b6))
* 新增结果的修改API ([aff7813](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/aff781380496f092de4b835698ad1b056e465005))
* 修改docker-compose 用于本地多服务开发调试 ([27d1527](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/27d1527dec66a7b09350c8f0ee35bdfcfc92d7be))
* 修改setting 临时紧急调试异常规避 ([5bc66c0](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/5bc66c0e479dcf3f2607e92ddeeff42e00420e97))
* 增加文件列表页中的文件大小 ([2d1d28a](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/2d1d28a7cafe562b41f9b171a73354cab87b40b6))
* 增加media 路径pdf 预览 ([740498e](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/740498e8e69eab3fa244c8bab25018bc757b84b4))


### Bug Fixes

* 文本抽取结果更新 ([501afba](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/501afbad5442d1847e3a7b67f7db67d809091ea3))

## [1.2.0-dev.0](https://github.com/iblofcqu/Corpus-automation-and-conversion/compare/v1.1.0...v1.2.0-dev.0) (2026-01-21)


### Features

* **docker:** 添加 Dockerfile 以支持项目容器化部署 ([00e5573](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/00e55737424922a8b01cc469ff6ff7b48c786c2a))

## [1.1.0](https://github.com/iblofcqu/Corpus-automation-and-conversion/compare/v1.0.0...v1.1.0) (2026-01-21)


### Features

* **settings:** 修改全局鉴权和APIS 部分的鉴权 ([fd9e5c1](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/fd9e5c1a630c1c1424576e2f43799890847cfb6c))

## 1.0.0 (2026-01-21)


### Features

* 基于AI agent 初版实现应用骨架 ([19c1a94](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/19c1a949f164d059d306541f70ac8d36e458c8f5))
* **apis:** 增加X-User-ID 到openapi 中 ([13c7c09](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/13c7c09525d61c269679824d5b09cf7a600d82e2))
* django app ([6af4ab5](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/6af4ab52a8300aea4650a65a1115e4466467803c))
* django project ([85ecccc](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/85ecccc5a55f598acb87c4dafbb3c1df6d6c8d6a))
* **init:** 增加MinerUConversionResult和MinerUError到导出列表 ([a41415a](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/a41415a8bf4bba4eb51b801e37339b6ebd3011a3))
* **mineru-service:** 确保返回的是相对路径 ([12b486c](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/12b486c4a08036f0e09e14fff2af659a9f3c7374))
* **mineru-service:** 完善对mineru http api 调用封装 ([9137603](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/9137603f808fe376746cc6ad7e891665957509f1))
* **OntologyService:** 文件exists 校验 ([cf9c5fb](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/cf9c5fb131b29fe2c92ae1ab763535d23201210d))
* **Step5-ontology:** 移除内嵌api-key 的写法 ([05e00a2](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/05e00a25d56a7d0b6507375d36c84666ebe06056))
* **Step5:** style pep8 change & 返回相对路径 ([52c6805](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/52c6805689a1199bf06bb9215bf4d586efd2209c))


### Bug Fixes

* **集成测试:** 计算完成循环跳出 ([1c5de4a](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/1c5de4abf9b95b0cb36d8840c34f5505e258d63d))
* **ontology-service:** 修改OntologyException为OntologyError，并更新相关抛出逻辑 ([87021be](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/87021be1a8699c09083edce75877af6dec751ac7))
* **process-pdf-task:** 传递可访问路径到pdf 提取函数中去 ([e0e428e](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/e0e428ebe92f3470db628e43926b7e2c1377db58))
* **ProjectCreateSerializer:** 未选择模板json时拷贝复制,以兼容既有逻辑 ([027c993](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/027c9936bfb764e5d54d2556ae4a411a82807d47))
* **tasks:** 从project 获取配置json ([8c5459d](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/8c5459daaa01534ef92589ba568a9762ffd9b133))
* **tasks:** 确保数据库中统一相对路径 ([975cad4](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/975cad479a378e8491e9d25dd73c750833b0e40e))
* **tasks:** 同步修改pdf 转文本后的上层调用 ([8d786d6](https://github.com/iblofcqu/Corpus-automation-and-conversion/commit/8d786d66598fe9a96bb03235a812285f8d0b624a))
