import time
import curses
import random
from itertools import cycle
from curses_tools import draw_frame, read_controls, get_frame_size


class EventLoopCommand():

    def __await__(self):
        return (yield self)


class Sleep(EventLoopCommand):

    def __init__(self, seconds):
        self.seconds = seconds


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    row, column = start_row, start_column
    canvas.addstr(round(row), round(column), '*')
    await Sleep(0.1)

    canvas.addstr(round(row), round(column), 'O')
    await Sleep(0.1)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await Sleep(0.1)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await Sleep(0.5 + random.randint(0, 2))

        canvas.addstr(row, column, symbol)
        await Sleep(0.3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await Sleep(0.5)

        canvas.addstr(row, column, symbol)
        await Sleep(0.3)


async def animate_spaceship(canvas, row, column, row_max, column_max, frames):
    for frame in cycle(frames):
        draw_frame(canvas, row, column, frame)
        await Sleep(0.1)
        draw_frame(canvas, row, column, frame, negative=True)
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
    stars = [
        (blink(
            canvas,
            *positions.pop(0),
            symbol=random.choice(stars_symbols)
        )) for i in range(stars_count)
    ]
    coroutines_with_timeout = [[0, star] for star in stars]  # звезды

    coroutines_with_timeout.append(
        [0, fire(canvas, max_y/2, max_x/2)]
    )
    frames = []
    with open("./animations/rocket_frame_2.txt", "r") as f:
        frames.append(f.read())
    with open("./animations/rocket_frame_1.txt", "r") as f:
        frames.append(f.read())
    coroutines_with_timeout.append(
        [0, animate_spaceship(canvas, max_y/2, max_x/2, max_y, max_x, frames)]
    )
    while coroutines_with_timeout:
        min_delay, _ = min(coroutines_with_timeout, key=lambda pair: pair[0])
        coroutines_with_timeout = [[timeout - min_delay, coroutine] for timeout, coroutine in coroutines_with_timeout]
        time.sleep(min_delay)
        # делим корутины на активные и спящие
        active_coroutines = [[timeout, coroutine] for timeout, coroutine in coroutines_with_timeout if timeout <= 0]
        coroutines_with_timeout = [[timeout, coroutine] for timeout, coroutine in coroutines_with_timeout if timeout > 0]
        for _, coroutine in active_coroutines:
            try:
                sleep_command = coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                continue  # выкидываем истощившуюся корутину
            seconds_to_sleep = sleep_command.seconds
            coroutines_with_timeout.append([seconds_to_sleep, coroutine])


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
