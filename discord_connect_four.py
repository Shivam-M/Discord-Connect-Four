import json
import discord

from discord.ext import commands
from datetime import datetime
from random import randint
from time import time


# TODO: Save scores and stats - done
# TODO: Handle ties correctly - done? not tested
# TODO: Implement .cancel command - done
# TODO: Optional: Custom rows/columns per match? - abandoned
# TODO: Handle multiple challenges (.accept [user])
# TODO: Implement find_user() - done
# TODO: Remove 'host' and 'user' keys in match dictionary, replace with 'players' list.


Client = discord.Client()
client = commands.Bot(command_prefix="[")

VALID_COMMANDS = {
    '.HELP': 1,
    '.STATS': 1,
    '.ACCEPT': 1,
    '.CANCEL': 1,
    '.CHALLENGE': 2,
}

HELP_MESSAGE = '''` COMMANDS 
 .accept - accept a match request 
 .stats [user] - view match stats
 .challenge <user> - challenge a user to a match 
 .cancel - cancel a challenge request `'''

TEAMS = ['●', '○']
game_matches = {}

with open('matches.json', 'r') as f:
    saved_matches = json.load(f)


def generate_number():
    match_number = str(randint(10000, 99999))
    if match_number not in game_matches:
        return match_number


def accept_match(acceptor):
    for match in game_matches:
        if acceptor == game_matches[match]['user']:
            game_matches[match]['phase'] = 'in-game'
            return True
    return False


def place_counter(match_id, column_number, player):
    game_board = game_matches[match_id]['board'].copy()
    if game_board[0][column_number] != '-':
        return False
    if game_board[5][column_number] == '-':
        game_board[5][column_number] = TEAMS[game_matches[match_id]['players'].index(player)]
        game_matches[match_id]['board'] = game_board.copy()
        return True
    for x in range(6):
        if game_board[x][column_number] != '-':
            game_board[x-1][column_number] = TEAMS[game_matches[match_id]['players'].index(player)]
            game_matches[match_id]['board'] = game_board.copy()
            return True


def handle_column(player, msg):
    match_id = playing_match(player)[1]
    if game_matches[match_id]['phase'] == 'in-game':
        if game_matches[match_id]['turn'] == player:
            try:
                column_number = int(msg[1])
                if column_number not in range(1, 8):
                    return
            except:
                return
            if not place_counter(match_id, column_number - 1, player):
                return
            if game_matches[match_id]['players'][0] == game_matches[match_id]['turn']:
                game_matches[match_id]['turn'] = game_matches[match_id]['players'][1]
            else:
                game_matches[match_id]['turn'] = game_matches[match_id]['players'][0]
            return True


def build_embed(match_id):
    match_info = game_matches[match_id]
    board = [inner_list[:] for inner_list in match_info['board']]
    match_board = ''
    for row in board:
        for x in row:
            if x == '-':
                row[row.index(x)] = ' '
        match_board += '| ' + ' | '.join(row) + '  |\n'
    embed = discord.Embed(title="SM#8389", color=0x141414)
    embed.add_field(name="**CONNECT FOUR**", value="**{0}'s turn**".format(match_info['turn'].display_name), inline=False)
    embed.add_field(name="{0}".format(match_info['players'][0].display_name), value=TEAMS[0], inline=True)
    embed.add_field(name="{0}".format(match_info['players'][1].display_name), value=TEAMS[1], inline=True)
    embed.add_field(name="**TABLE**", value='```' + match_board + '```', inline=False)
    return embed


def check_win(board, team):
    for y in range(6):
        for x in range(4):
            if board[y][x] == team and board[y][x + 1] == team:
                if board[y][x + 2] == team and board[y][x + 3] == team:
                    return True
    for y in range(3):
        for x in range(7):
            if board[y][x] == team and board[y + 1][x] == team:
                if board[y + 2][x] == team and board[y + 3][x] == team:
                    return True
    for y in range(3):
        for x in range(7):
            if board[y][x] == team:
                try:
                    if board[y + 1][x - 1] == team:
                        if board[y + 2][x - 2] == team:
                            if board[y + 3][x - 3] == team:
                                return True
                except IndexError:
                    pass
                try:
                    if board[y + 1][x + 1] == team:
                        if board[y + 2][x + 2] == team:
                            if board[y + 3][x + 3] == team:
                                return True
                except IndexError:
                    pass
    return False


def check_tie(board):
    for row in board:
        for x in row:
            if x == '-':
                return False
    return True


def end_match(match_id, winner=None):
    # TODO -> Consider saving board for replays
    for data in ['turn', 'phase', 'host', 'user', 'board']:
        del game_matches[match_id][data]
    if winner:
        game_matches[match_id]['winner'] = winner.id
    else:
        game_matches[match_id]['winner'] = 'None'
    game_matches[match_id]['players'][0] = game_matches[match_id]['players'][0].id
    game_matches[match_id]['players'][1] = game_matches[match_id]['players'][1].id
    saved_matches[f'{int(time())}-{match_id}'] = game_matches[match_id]
    del game_matches[match_id]
    with open('matches.json', 'w') as matches_file:
        json.dump(saved_matches, matches_file, indent=4)


def build_stats(user, server):
    user_id = user.id
    match_outcomes = {'Won': 0, 'Lost': 0, 'Tied': 0}
    embed = discord.Embed(title="SM#8389", color=0x141414)
    embed.add_field(name="**CONNECT FOUR**", value="**{0}'s stats**".format(user.display_name), inline=False)
    for match in saved_matches:
        # TODO: Handle user leave
        if user_id in saved_matches[match]['players']:
            match_id = match.split("-")[1]
            opponent_id = saved_matches[match]['players'][saved_matches[match]['players'].index(user.id) - 1]
            match_time = datetime.utcfromtimestamp(int(match.split("-")[0])).strftime('%H:%M')
            match_date = datetime.utcfromtimestamp(int(match.split("-")[0])).strftime('%d-%m-%Y')
            if saved_matches[match]['winner'] == user_id:
                match_outcome = 'Won'
            elif saved_matches[match]['winner'] == opponent_id:
                match_outcome = 'Lost'
            else:
                match_outcome = 'Tied'
            match_outcomes[match_outcome] += 1
            embed.add_field(name=f"> Match **#{match_id}** at _**{match_time}** on **{match_date}**_", value=f'> **{match_outcome}** against **{server.get_member(opponent_id)}**', inline=False)
    embed.add_field(name='**WINS**', value=f'`     {match_outcomes["Won"]}     `', inline=True)
    embed.add_field(name='**LOSSES**', value=f'`     {match_outcomes["Lost"]}     `', inline=True)
    embed.add_field(name='**TIES**', value=f'`     {match_outcomes["Tied"]}     `', inline=True)
    return embed


def playing_match(user):
    for match in game_matches:
        if user in game_matches[match]['players']:
            return [True, match]
    return [False]


def create_match(creator, user):
    game_matches[generate_number()] = {
        'phase': 'waiting',
        'host': creator,
        'user': user,
        'players': [creator, user],
        'board': [['-' for x in range(7)] for y in range(6)],
        'winner': None,
        'turn': creator
    }


@client.event
async def on_ready():
    print("Connected!")


def find_user(message, arg):
    if message.mentions:
        return message.mentions[0]
    for member in message.guild.members:
        if member.display_name.upper() == arg:
            return member
    return


@client.event
async def on_message(message):
    if message.author.bot is False:
        msg = message.content.upper()
        args = msg.split(' ')
        if msg[0] == '^':
            if not playing_match(message.author)[0]:
                await message.channel.send("`ERROR:` `You cannot use this command, you're not in a match.`"); return
            if handle_column(message.author, msg):
                await message.channel.send(embed=build_embed(playing_match(message.author)[1]))
                match_id = playing_match(message.author)[1]
                if check_win(game_matches[match_id]['board'], TEAMS[game_matches[match_id]['players'].index(message.author)]):
                    await message.channel.send(f"`GAME:` `Four in a row! {message.author.display_name} won the game.`")
                    end_match(match_id, message.author)
                elif check_tie(game_matches[match_id]['board']):
                    await message.channel.send(f"`GAME:` `The match between {game_matches[playing_match(message.author)[1]]['user'].display_name} and {game_matches[playing_match(message.author)[1]]['host'].display_name} resulted in a tie!`")
                    end_match(match_id)
        if args[0] not in VALID_COMMANDS:
            return
        if len(args) < VALID_COMMANDS[args[0]]:
            await message.channel.send("`ERROR:` `Invalid command arguments, type .help to view command usage.`"); return
        if args[0] == '.HELP':
            await message.channel.send(HELP_MESSAGE)
        elif args[0] == '.STATS':
            if len(args) == 1:
                await message.channel.send(embed=build_stats(message.author, message.guild))
            else:
                if find_user(message, args[1]):
                    await message.channel.send(embed=build_stats(find_user(message, args[1]), message.guild))
                else:
                    await message.channel.send('`ERROR`: `Player could not be found.`')
        elif args[0] == '.ACCEPT':
            if not playing_match(message.author)[0]:
                await message.channel.send("`ERROR:` `You cannot use this command right now.`"); return
            if not accept_match(message.author):
                await message.channel.send("`ERROR:` `No match was found for you to accept.`")
            else:
                await message.channel.send(f"`GAME:` `{message.author.display_name} accepted {game_matches[playing_match(message.author)[1]]['host'].display_name}'s challenge!`")
                await message.channel.send(f"`GAME:` `To enter a column number, type ^X where X is a number from 1 to 7.`")
                await message.channel.send(embed=build_embed(playing_match(message.author)[1]))
        elif args[0] == '.CANCEL':
            if not playing_match(message.author)[0]:
                await message.channel.send("`ERROR:` `You do not have a current active challenge.`"); return
            match_id = playing_match(message.author)[1]
            if game_matches[match_id]['phase'] == 'waiting':
                await message.channel.send(f"`GAME:` `Cancelled your challenge request against {game_matches[match_id]['user'].display_name}.`")
                del game_matches[match_id]
            else:
                await message.channel.send(f"`GAME:` `This command cannot be used right now.`")
        elif args[0] == '.CHALLENGE':
            if playing_match(message.author)[0]:
                await message.channel.send("`ERROR:` `You cannot use this command while you have an active match or challenge request.`"); return
            if message.mentions:
                if message.mentions[0] == message.author or args[1] == message.author.display_name.upper():
                    await message.channel.send("`ERROR:` `You cannot challenge yourself!`"); return
            target_user = find_user(message, args[1])
            if not target_user:
                await message.channel.send("`ERROR:` `Could not find the user, make sure you spelt their name correctly.`"); return
            if playing_match(target_user)[0]:
                await message.channel.send("`ERROR:` `This player is already in a match.`"); return
            create_match(message.author, target_user)
            await message.channel.send(f"`GAME:` `{message.author.display_name} challenged {target_user.display_name} to a match! Type .accept to respond.`")


print("Attempting to run the BOT...")
client.run(open('client-token.txt', 'r').read().rstrip())
