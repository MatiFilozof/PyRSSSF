import csv

from entities.Competitions import competition_dictionary, CompetitionInstance, Relegation, Promotion


class Team:
    def __init__(self, fb):
        self.fb = fb


class TeamDictionary:
    def __init__(self):
        self.teams = dict()

    def get(self, team):
        # TODO maybe write separate teams.csv for each country? there's overlap between e.g. Faroes and Iceland,
        #  for example Vikingur; or add country as additional parameter
        while not self.teams.__contains__(team):
            decision = input('Missing entry for {0}.\n'
                             'Type "1" to associate with other entry.\n'
                             'Type "2" to provide new fb name.\n'
                             'Type "3" to assign temporary fb name (use for entries with typos).\n'
                             'Type "0" to skip this line.'.format(team))
            if decision == '1':
                key = input('Provide key of the other entry to associate with.')
                if self.teams.__contains__(key):
                    self.teams.__setitem__(team, self.teams.get(key))
                    with open("teams.csv", 'a+', encoding='utf-8') as f:
                        f.write("{0},{1}\n".format(team, self.teams.get(key).fb))
                else:
                    print('Key doesn\'t exist!')
            elif decision == '2':
                fb_name = input('Provide fb name for new team.')
                self.teams.__setitem__(team, Team(fb_name))
                with open("teams.csv", 'a+', encoding='utf-8') as f:
                    f.write("{0},{1}\n".format(team, fb_name))
            elif decision == '3':
                fb_name = input('Provide fb name for this entry.')
                self.teams.__setitem__(team, Team(fb_name))
            elif decision == '0':
                return None
        return self.teams.get(team)


team_dictionary = TeamDictionary()
d = dict()
with open("teams.csv", 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for line in reader:
        d[line[0]] = Team(line[1])
team_dictionary.teams = d


class Table:
    def __init__(self, source, points_per_win=3):
        self.source = source
        self.ppw = points_per_win
        self.standings = dict()
        self.competitions = dict()

    def add_row(self, position, team, wins, draws, losses, goals_scored, goals_conceded):
        self.standings.__setitem__(position,
                                   TableRow(position, team, wins, draws, losses, goals_scored, goals_conceded))
        self.competitions.__setitem__(position, None)
        return self

    def add_competitions(self):
        finished = False
        while not finished:
            key = input('Select competition. Leave empty if no more competitions to be added.')
            if not key:
                finished = True
            else:
                c = CompetitionInstance(competition_dictionary.get(key))
                c_season = input('Provide season. Leave empty if not applicable.')
                if c_season:
                    c.season = c_season
                c_round = input('Provide round. Leave empty if not applicable.')
                if c_round:
                    c.round = c_round
                c_note = input('Provide note. Leave empty if not applicable.')
                if c_note:
                    c.note = c_note
                positions = input('Provide positions to apply competition to. If multiple, separate them by ",".')
                positions = positions.split(",")
                for pos in positions:
                    self.competitions.__setitem__(int(pos.strip()), c)
        return self

    def add_relegations(self):
        self.add_league_change(True)

    def add_promotions(self):
        self.add_league_change(False)

    def add_league_change(self, down=True):
        league = input("Provide league to {0} to. Leave empty if none to add.".format("relegate" if down else "promote"))
        if league:
            season = input('Provide season. Leave empty if not applicable.')
            # notes are disabled by default, for they are unnecessary
            # note = input('Provide note. Leave empty if not applicable.')
            event = Relegation(league, season, None) if down else Promotion(league, season, None)
            positions = input('Provide positions to apply this event to. If multiple, separate them by ",".')
            positions = positions.split(",")
            for pos in positions:
                self.competitions.__setitem__(int(pos.strip()), event)

    def to_wiki(self, filename):
        with open(filename, 'a+', encoding='utf-8') as f:
            notes = []

            f.write("== Tabela ==\n")
            f.write("{{Fb cl header}}\n")
            # mark last position with competition added so that two consecutive positions aren't marked twice
            last_competition_position = 0
            for position in self.standings.keys():
                rowspan = 0
                if self.competitions.get(position - 1) and not self.competitions.get(position):
                    rowspan = min([key for key, entry in self.competitions.items() if key > position and entry] +
                                  [max(self.competitions.keys()) + 1]) - position

                if self.standings.get(position).points_deducted[1]:
                    notes.append(self.standings.get(position).points_deducted[1])

                f.write("{{{{Fb cl team {0}|p={1:<2}|{2}{3}{4}}}}}{5}\n".format(
                    "2pts " if self.ppw == 2 else "",
                    position,
                    self.standings.get(position).to_wiki(color=not self.competitions.get(position)),
                    "|bc={0}".format(self.competitions.get(position).get_color()) if self.competitions.get(position) else "",
                    "|pn={0}".format(len(notes)) if self.standings.get(position).points_deducted[1] else "",
                    "||rowspan={0}|".format(rowspan) if rowspan > 0 else ""
                ))

                if self.competitions.get(position) and position > last_competition_position:
                    competition = self.competitions.get(position)
                    rows = 1
                    while self.competitions.__contains__(position + rows) and \
                            self.competitions.get(position + rows) and \
                            (competition == self.competitions.get(position + rows)):
                        last_competition_position = position + rows
                        rows += 1

                    if competition.note:
                        notes.append(competition.note)
                    f.write(competition.to_wiki(rows, len(notes)))

            wiki_notes = ""
            if len(notes) > 0:
                wiki_notes = "|nt="
                for index, note in enumerate(notes):
                    if index > 0:
                        wiki_notes += "<br />"
                    wiki_notes += "<sup>{0}</sup>{1}".format(index + 1, note)
            f.write("{{{{Fb cl footer |s=[{0}] {{{{lang|en}}}} {1}}}}}\n\n".format(self.source, wiki_notes))


class TableRow:
    def __init__(self, position, team, wins, draws, losses, goals_scored, goals_conceded):
        self.position = position
        self.team = team_dictionary.get(team)
        self.wins = wins
        self.draws = draws
        self.losses = losses
        self.gf = goals_scored
        self.ga = goals_conceded
        # additional info
        self.points_deducted = (0, None)
        self.champions = False
        self.relegation = False
        self.promotion = False

    def set_champions(self):
        self.champions = True
        return self

    def set_relegation(self):
        self.relegation = True
        return self

    def set_promotion(self):
        self.promotion = True
        return self

    def deduct_points(self, points, note):
        self.points_deducted = (points, note)
        return self

    def to_wiki(self, color=True):
        color_wiki = "#FFFF00" if self.champions else "#FFCCCC" if self.relegation else None
        wiki = "t={0:<25}|w={1:<2}|d={2:<2}|l={3:<2}|gf={4:<3}|ga={5:<3}{6}{7}{8}{9}{10}".format(
            self.team.fb, self.wins, self.draws, self.losses, self.gf, self.ga,
            "|dp={0}".format(self.points_deducted[0]) if self.points_deducted[0] > 0 else "",
            "|champion=y" if self.champions else "",
            "|relegated=y" if self.relegation else "",
            "|promoted=y" if self.promotion else "",
            "|bc={0}".format(color_wiki) if color_wiki and color else ""
        )
        return wiki
