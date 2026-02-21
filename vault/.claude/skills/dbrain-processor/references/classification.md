# Entry Classification

## Work Domains → Categories

Based on user context (see [about.md](about.md)):
Евгений Семеев — эксперт Horeca в Ташкенте. Клиенты: кофейни, рестораны, ночные заведения, сетки с высоким чеком.

### Клиентские проекты Horeca
Управление, сервис, персонал, тренинги, консалтинг, заведения

**Keywords:** кофейня, ресторан, бар, ночной клуб, заведение, гости, персонал, управляющий, сервис, клиентский, чек, бриф, дедлайн, клиент, презентация, KPI, стандарты

**→ Category:** task (p1-p2) → Todoist

### Личный бренд & Контент
Telegram-канал, лекции, выступления, контент, узнаваемость

**Keywords:** канал, пост, лекция, выступление, тренинг, контент, аудитория, подписчики, личный бренд, Семеев, репутация, статья, тезис

**→ Category:** idea или task (если с дедлайном) → thoughts/ideas/ или Todoist

### AI & Технологии
Второй мозг, инструменты, автоматизация

**Keywords:** Claude, GPT, бот, агент, автоматизация, второй мозг, инструмент, API, промпт, Todoist

**→ Category:** learning или project → thoughts/learnings/

### Деньги & Инвестиции
Доход, контракты, партнёрства, инвестиции, ремонт

**Keywords:** деньги, доход, контракт, оплата, партнёрство, инвестиция, ремонт, бюджет, смета, финансы

**→ Category:** task (p2-p3) → Todoist

### Обучение & Рост
Профайлинг, психотипы, английский, навыки

**Keywords:** профайлер, психотип, английский, курс, книга, навык, изучить, разобраться, понял, узнал

**→ Category:** learning → thoughts/learnings/

### Личное
Семья, отдых, здоровье, дом

**Keywords:** Мадина, Селин, семья, PUBG, байк, дом, ремонт, здоровье, отдых, личное

**→ Category:** reflection или task (если требует действия) → thoughts/reflections/

---

## Decision Tree

```
Entry text contains...
│
├─ Заведение / клиент / персонал / дедлайн? ────> TASK (p1-p2) → Todoist
│  (кофейня, ресторан, гости, сервис, KPI)
│
├─ Деньги / контракт / ремонт? ─────────────────> TASK (p2-p3) → Todoist
│  (доход, оплата, смета, бюджет)
│
├─ Личный бренд / контент с дедлайном? ─────────> TASK (p2-p3) → Todoist
│  (пост до пятницы, лекция, выступление)
│
├─ Идея для канала / контент без дедлайна? ──────> IDEA → thoughts/ideas/
│  (пост, тезис, тема для выступления)
│
├─ Что-то узнал / инсайт? ───────────────────────> LEARNING → thoughts/learnings/
│  (понял, узнал, профайлинг, инструмент)
│
├─ Личное размышление? ──────────────────────────> REFLECTION → thoughts/reflections/
│  (осознал, семья, цели, философия)
│
└─ Операционная задача? ─────────────────────────> TASK (p3) → Todoist
   (позвонить, написать, договориться)
```

## Decision Filters для Евгения

Перед сохранением спроси:
- Это строит личный бренд Евгений Семеев?
- Это принесёт реальные деньги?
- Это масштабируется?
- Интуиция говорит «да»?

Если да на 2+ вопроса → повысить приоритет.

**СДВГ-правило:** Любую большую задачу разбивать на конкретные шаги. Никаких "разобраться с..." или "подумать о..."

---

## Photo Entries

For `[photo]` entries:

1. Analyze image content via vision
2. Determine domain:
   - Скриншот из заведения / меню / интерьер → Horeca проект
   - Схема / диаграмма → AI & Tech или проект
   - Текст / статья → Learning
3. Add description to daily file

---

## Output Locations

| Category | Destination | Priority |
|----------|-------------|----------|
| task (клиент/Horeca) | Todoist | p1-p2 |
| task (деньги/контракт) | Todoist | p2-p3 |
| task (личный бренд с дедлайном) | Todoist | p2-p3 |
| task (операционное) | Todoist | p3 |
| idea | thoughts/ideas/ | — |
| reflection | thoughts/reflections/ | — |
| project | thoughts/projects/ | — |
| learning | thoughts/learnings/ | — |

---

## File Naming

```
thoughts/{category}/{YYYY-MM-DD}-short-title.md
```

Examples:
```
thoughts/ideas/2026-02-21-telegram-channel-content-plan.md
thoughts/learnings/2026-02-21-profliling-insight.md
thoughts/reflections/2026-02-21-tashkent-fresh-start.md
```

---

## Thought Structure

```markdown
---
date: {YYYY-MM-DD}
type: {category}
domain: {Horeca|Личный бренд|Деньги|Обучение|Личное}
tags: [tag1, tag2]
---

## Context
[Что привело к мысли]

## Insight
[Ключевая идея]

## Implication
[Что это значит для бренда Евгений Семеев / дохода / роста]

## Next Action
[Конкретный шаг — не абстрактный]
```

---

## Anti-Patterns (ИЗБЕГАТЬ)

- "Подумать о..." → конкретизировать немедленно
- "Разобраться с..." → что конкретно сделать?
- Абстрактные задачи без Next Action
- Задачи без дат
- Игнорировать СДВГ-контекст — всегда дробить на шаги

---

### AI & Digital Content (добавлено)
YouTube, видеогенерация, страшные истории, экранизации книг

**Keywords:** YouTube, видео, генерация, Runway, Sora, Midjourney, страшная история, экранизация, книга, AI-контент, монетизация канала, подписчики

**→ Category:** idea или project → thoughts/ideas/ или thoughts/projects/

**Логика:** Если идея для видео — сохранить в ideas. Если это конкретный проект с шагами — в projects.
