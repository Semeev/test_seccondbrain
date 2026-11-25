"""Button handlers for reply keyboard."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from d_brain.bot.keyboards import (
    BTN_DO,
    BTN_HELP,
    BTN_PROCESS,
    BTN_STATUS,
    BTN_WEEKLY,
    labels,
)
from d_brain.bot.states import DoCommandState

router = Router(name="buttons")


@router.message(F.text.in_(labels(BTN_STATUS)))
async def btn_status(message: Message) -> None:
    """Handle Status button."""
    from d_brain.bot.handlers.commands import cmd_status

    await cmd_status(message)


@router.message(F.text.in_(labels(BTN_PROCESS)))
async def btn_process(message: Message) -> None:
    """Handle Process button."""
    from d_brain.bot.handlers.process import cmd_process

    await cmd_process(message)


@router.message(F.text.in_(labels(BTN_WEEKLY)))
async def btn_weekly(message: Message) -> None:
    """Handle Weekly button."""
    from d_brain.bot.handlers.weekly import cmd_weekly

    await cmd_weekly(message)


@router.message(F.text.in_(labels(BTN_DO)))
async def btn_do(message: Message, state: FSMContext) -> None:
    """Handle Do button - set state and wait for input."""
    from d_brain.bot.handlers.do import ASK_PROMPT

    await state.set_state(DoCommandState.waiting_for_input)
    await message.answer(ASK_PROMPT)


@router.message(F.text.in_(labels(BTN_HELP)))
async def btn_help(message: Message) -> None:
    """Handle Help button."""
    from d_brain.bot.handlers.commands import cmd_help

    await cmd_help(message)
