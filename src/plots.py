import math
import matplotlib.pyplot as plt
from matplotlib import dates as md
from matplotlib import rcParams


def plot_statistics(df, players):
    """Рисует картинку statistics.png на основе данных в statistics.csv."""
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.size'] = 8

    fig = plt.figure(figsize=(10, 8))
    # Расстояние между графиками
    # fig.subplots_adjust(hspace=0.15)

    # Bar Chart settings
    ax1 = fig.add_subplot(211)  # nrows, ncols, index
    ax1.set_xlabel('PLAYERS')
    ax1.set_ylabel('WINS / LOSES')
    ax1.grid(True, linestyle='dotted', axis='y')
    ax1.set_title(df.iloc[-1, 0].strftime("%Y/%m/%d %H:%M:%S"))

    colors = ['#2ca02c', '#ff7f0e', '#1f77b4', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    hatches = []

    wins = [df[str(player_id)].sum().real for player_id in players]
    loses = [df[str(player_id)].sum().imag for player_id in players]

    val_min, val_max = min(wins), max(wins)
    for val in wins:
        if val == val_max:
            hatches.append('*')
        elif val == val_min:
            hatches.append('o')
        else:
            hatches.append(None)

    # Line Chart Settings
    ax2 = fig.add_subplot(223)  # nrows, ncols, index
    ax2.set_xlabel('GAME DATES')
    ax2.set_ylabel('WINS, %')
    ax2.grid(which='both', linestyle='dotted')
    ax2.xaxis.set_major_formatter(md.DateFormatter('%Y\n%m/%d'))
    ax2.tick_params(axis='x', labelsize=7)

    # Quiver Chart Settings
    ax3 = fig.add_subplot(224)  # nrows, ncols, index
    ax3.set_xlabel('LOSES')
    ax3.set_ylabel('WINS')
    ax3.grid(which='both', linestyle='dotted')

    # Bar plot
    x_labels = [players[player_id][1] for player_id in players]
    ax1.bar(x_labels, wins, align='edge', width=-0.2, color=colors, hatch=hatches, edgecolor='white')
    ax1.bar(x_labels, loses, align='edge', width=0.125, hatch='////',
            color='white', edgecolor='black', label='Количество поражений')

    # Line plot
    def calculate_percent(x):
        if x.real + x.imag:
            return round(x.real / (x.real + x.imag) * 100, 2)
        else:
            return 0

    for idx, player_id in enumerate(players):
        ax2.plot(df['datetime'],
                 df[str(player_id)].cumsum().apply(calculate_percent),
                 label=players[player_id][1],
                 marker='o',
                 markersize=4,
                 linestyle='-',
                 markerfacecolor='none',
                 color=colors[idx])

    # Quiver plot
    re_max = 0
    im_max = 0
    for idx, player_id in enumerate(players):

        player_statistic = df[str(player_id)].sum()
        re = int(player_statistic.real)
        im = int(player_statistic.imag)
        experience = round(abs(player_statistic), 1)
        efficiency = round(math.atan2(re, im) / math.pi * 180, 1)
        if re:
            win_percent = round(re / (re + im) * 100, 1)
        else:
            win_percent = 0
        ax3.quiver(0, 0, im, re,
                   angles='xy',
                   scale_units='xy',
                   color=colors[idx],
                   scale=1,
                   label=players[player_id][1])

        ax3.annotate(f'{experience}|{efficiency}° ({win_percent}%)', (im, re), fontsize=6.5)

        if re > re_max:
            re_max = re
        if im > im_max:
            im_max = im

    if re_max:
        ax3.set_ylim([0, re_max + 0.3 * re_max])
    if im_max:
        ax3.set_xlim([0, im_max + 0.3 * im_max])

    ax1.legend()
    ax2.legend(fontsize='x-small')
    ax3.legend(loc='lower right', fontsize='small')

    fig.savefig('statistics_data/statistics.png', dpi=300, bbox_inches='tight')
