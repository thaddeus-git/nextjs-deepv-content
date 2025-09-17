# DeepV Code Content Repository

This repository contains all articles and content for the DeepV Code documentation website.

## Structure

```
├── config/
│   ├── article-index.json    # Article metadata index
│   └── categories.json       # Category configuration
├── guides/
│   └── *.mdx                # Article files
└── staging/
    ├── guides/              # Staging area for new articles
    └── config/              # Staging configuration
```

## Usage

This repository is automatically fetched during the build process of the main Next.js application.

## Article Format

Each article should be an MDX file with the following frontmatter:

```yaml
---
title: "Article Title"
slug: "article-slug"
category: "category-name"
subcategory: "subcategory-name"
description: "Brief description"
difficulty: "beginner" | "intermediate" | "advanced"
readTime: 30
publishedAt: "2025-01-01"
featured: true
technology: "Technology Name"
tags:
  - "tag1"
  - "tag2"
---
```

## Deployment

When articles are updated in this repository, the main website will automatically revalidate the content within 1 hour, or immediately via webhook.
