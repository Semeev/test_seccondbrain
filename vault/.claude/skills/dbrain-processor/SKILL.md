---
name: second-brain-processor
description: Daily processor for Telegram entries → Todoist tasks + Obsidian notes + HTML report.
---

# Second Brain Processor

## Output: RAW HTML only
No markdown. No code blocks. Start directly with content.
Tags allowed: `<b>` `<i>` `<code>` `<s>` `<u>`
Max 4096 chars.

## Flow

1. Read `goals/3-weekly.md` → ONE Big Thing
2. `find-tasks-by-date` (today + 7 days) → workload
3. `find-tasks` labels: ["process-goal"] → check process goals
4. Read `daily/YYYY-MM-DD.md` → classify entries
5. For each entry → create task/note (see table below)
6. Log actions to daily file
7. Update `MEMORY.md` if context changed
8. Return HTML report

## Entry → Output

| Type | Todoist | Obsidian |
|------|---------|----------|
| Задача | ✅ create | ✅ thoughts/tasks/YYYY-MM-DD-slug.md |
| Идея | ❌ | ✅ thoughts/ideas/ |
| Рефлексия | ❌ | ✅ thoughts/reflections/ |
| Инсайт/цитата | ❌ | ✅ thoughts/learnings/ |

**Каждая задача = Todoist + файл в thoughts/tasks/. Без исключений.**

## MCP Tools

- `find-tasks-by-date` — workload check
- `find-tasks` — duplicates / process-goals
- `add-tasks` — create tasks
- `complete-tasks` / `update-tasks` — modify

**Вызывай напрямую. Никогда не пиши "добавь вручную".**

## Priority

p1 — клиентский дедлайн / срочно
p2 — ONE Big Thing / деньги
p3 — цели года
p4 — операционное

## Process Goals

При каждом /process проверь `find-tasks` labels: ["process-goal"].
Если нет → создай recurring tasks из goals/ (max 5-7).

## HTML Report Template

📊 <b>Обработка за {DATE}</b>

<b>🎯 Фокус:</b> {ONE_BIG_THING}

<b>📓 Мысли:</b> {N}
• {emoji} {title} → {category}/

<b>✅ Задачи:</b> {M}
• {task} <i>({priority}, {due})</i>

<b>📋 Process Goals:</b>
• {goal} → {status}

<b>📅 Неделя:</b> Пн:{n} Вт:{n} Ср:{n} Чт:{n} Пт:{n}

<b>⚡ Топ-3:</b>
1. {task}
2. {task}
3. {task}

---
<i>Обработано за {duration}</i>

## References

- references/about.md — профиль пользователя
- references/classification.md — классификация
- references/todoist.md — задачи
- references/process-goals.md — process goals
