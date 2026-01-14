---
layout: default
title: Home
nav_order: 1
has_children: true
---

# SmithPy ⛏

**SmithPy** is a modern, opinionated CLI tool for building, validating, and managing **Minecraft modpacks** using the **Modrinth API v2**.

It focuses on **deterministic mod resolution**, **policy‑based dependency handling**, and **schema‑driven configuration**.

---

## ✨ Features

* 📦 Modrinth-first mod resolution
* 🧠 Policy engine for conflicts and sub‑mods
* 📜 JSON/YAML schema validation
* ⚙️ Designed for automation and CI
* 🐍 Distributed as a Python CLI via PyPI

---

## 🚀 Installation

Recommended (via PyPI):

```bash
pipx install smithpy
```

Alternative (virtualenv):

```bash
pip install smithpy
```

---

## 📚 Documentation

* 📄 [Schemas Overview](./schemas.md)
* 🧩 [Policy Schema](./schemas/policy.schema.json)
* 🔌 [Modrinth API Schema](./schemas/modrinth_api.schema.json)

---

## 🔗 Links

* 💻 [GitHub Repository](https://github.com/Frank1o3/smithpy)
* 🐞 [Issue Tracker](https://github.com/Frank1o3/smithpy/issues)
* 📦 [PyPI Project](https://pypi.org/project/smithpy)

---

## 🧪 Project Status

SmithPy is **actively developed**.

APIs and schemas are considered **stable**, while higher‑level CLI features continue to evolve.

Feedback and contributions are welcome.
