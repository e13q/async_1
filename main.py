import time
import curses
import random
import asyncio
from itertools import cycle
from curses_tools import draw_frame, read_controls, get_frame_size


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    row, column = start_row, start_column
    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*', offset_tics=0):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for i in range(5 + offset_tics):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for i in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for i in range(3):
            await asyncio.sleep(0)


async def animate_spaceship(canvas, row, column, row_max, column_max, frames):
    for frame in cycle(frames):
        row_dir, column_dir, space = read_controls(canvas)
        frame_size_rows, frame_size_columns = get_frame_size(frame)
        if row_dir > 0 and row + frame_size_rows < row_max - 1:
            row += row_dir
        elif row_dir < 0 and row > 1:
            row += row_dir
        if column_dir > 0 and column + frame_size_columns < column_max - 1:
            column += column_dir
        elif column_dir < 0 and column > 1:
            column += column_dir
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)


def draw(canvas):
    canvas.border()
    canvas.refresh()
    curses.curs_set(False)
    canvas.nodelay(True)
    max_y, max_x = canvas.getmaxyx()
    stars_symbols = ['+', '*', '.', ':']
    stars_count = 115
    possible_positions = [(y, x) for y in range(1, max_y - 1) for x in range(1, max_x - 1)]
    positions = random.sample(possible_positions, k=stars_count)
    coroutines = [
        (blink(
            canvas,
            *positions.pop(0),
            symbol=random.choice(stars_symbols),
            offset_tics=random.randint(0, 20)
        )) for i in range(stars_count)
    ]  # звезды

    coroutines.append(
        fire(canvas, max_y/2, max_x/2)
    )  # выстрел

    frames = []
    with open("./animations/rocket_frame_2.txt", "r") as f:
        frame = f.read()
        frames.append(frame)
        frames.append(frame)
    with open("./animations/rocket_frame_1.txt", "r") as f:
        frame = f.read()
        frames.append(frame)
        frames.append(frame)
    coroutines.append(
        animate_spaceship(canvas, max_y/2, max_x/2, max_y, max_x, frames)
    )  # корабль
    while coroutines:
        time.sleep(1)
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
