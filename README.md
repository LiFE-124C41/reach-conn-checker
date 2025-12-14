# reach-conn-checker

**Network Reachability & Connection Stability Checker**
*(ネットワーク到達性および接続安定性確認ツール)*

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Status](https://img.shields.io/badge/status-stable-green)

## 概要 (Overview)

`reach-conn-checker` は、ローカルおよびリモートホスト間の接続状態をシミュレーションし、パケットの到達性を監視するためのCLIツールです。
開発環境やステージング環境における、擬似的なトラフィック負荷テスト（Load Testing）に使用します。

**注意:** 本ツールはシミュレーターであり、実際のネットワーク設定を変更することはありません。

## インストール (Installation)

```bash
git clone https://github.com/your-repo/reach-conn-checker.git
cd reach-conn-checker
pip install .

# Windows環境の場合、TUI表示のために追加パッケージが必要です
pip install windows-curses
```

## 使い方 (Usage)

以下のコマンドで監視モードを開始します。

```bash
reach-conn-checker
# または
python -m reach_conn_checker
```

終了するには `exit` コマンドを入力するか、`Ctrl+C` を押してください。

---

<!--
🤫 Internal Documentation (For Developers)
-->

## 🤫 Internal Documentation (For Developers)

**※ここから先は開発者（プレイヤー）向けのマニュアルです。**

本ソフトウェアは、CLIで動作する **ステルス麻雀ゲーム** です。
画面上ではネットワークログが流れているようにしか見えませんが、内部では麻雀の対局が進行します。

### 特徴

- **完全なステルスUI**: 牌や点棒、アクションはすべて「ネットワークログ」「パケット情報」「メモリ番地」として表示されます。
- **Boss-Key 対応**: 緊急時に `exit` コマンドで即座に「正常終了ログ」を出して終了します。
- **シングルプレイ専用**: 外部通信を行わないため、社内ネットワーク等のパケット監視に引っかかることはありません（CPU対戦）。

### 画面の見方 (Decoding the Log)

画面には常に最新の「パケット（手牌）」が表示されます。

#### 1. 牌（Tile）の対応表

各牌は、以下のようなIPアドレスやポート番号、ステータスコードに偽装されます。

| 種類 | ゲーム内での意味 | 表示 (Log Output) | 覚え方 |
| :--- | :--- | :--- | :--- |
| **萬子 (Manzu)** | 1m ~ 9m | `ADDR_10` ~ `ADDR_19` | `10` + 数 |
| **筒子 (Pinzu)** | 1p ~ 9p | `PROC_20` ~ `PROC_29` | `20` + 数 |
| **索子 (Souzu)** | 1s ~ 9s | `THRD_30` ~ `THRD_39` | `30` + 数 |
| **風牌 (Winds)** | 東・南・西・北 | `HOST_E`, `HOST_S`, `HOST_W`, `HOST_N` | Hostname |
| **三元牌 (Dragons)** | 白・發・中 | `[NULL]`, `[G_O_F]`, `[R_E_D]` | 空, Green, Red |

#### 2. アクション (Actions)

コマンドラインへの入力は、シェルコマンドに見せかけます。

- **打牌 (Discard)**:
    - `ping <index>`: 手牌の左から `0`, `1`, `2`... のインデックス番号のパケットを破棄します。
    - ログ: `Packet forwarded: [Tile]`
- **ロン/ツモ (Win)**:
    - `sudo`: 手牌完成時に実行。
    - CPUの捨て牌でロン可能な場合、`OPPORTUNITY` 通知が出るので、その直後に `sudo` すればロンになります。
    - ログ: `[SUCCESS] CONNECTION ESTABLISHED`
- **リーチ (Reach)**:
    - `ping -t`: 聴牌（テンパイ）確認を行い、可能であれば自動モード（Continuous Ping）に移行します。
    - ログ: `Warning: Continuous ping initiated. Latency check started.`

### 開発ロードマップ

- [x] **Core Logic**: 麻雀の基本的な役判定ロジックの実装（パケット整合性チェック済み）
- [x] **Reach Feature**: リーチ（Continuous Ping）の実装
- [x] **AI Simulation**: 敵CPU（トラフィックジェネレーター）との1on1対戦モード
- [x] **UI Polish**: curses ライブラリを使用した、よりリアルなターミナル画面の構築