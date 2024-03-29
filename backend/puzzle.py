import random, re, time, string
from copy import copy as duplicate
 
# optional, speeds up by a factor of 4
# import psyco
# psyco.full()
 
class Crossword(object):
    def __init__(self, cols, rows, empty = '-', maxloops = 2000, available_words=[]):
        self.cols = cols
        self.rows = rows
        self.empty = empty
        self.maxloops = maxloops
        self.available_words = available_words
        self.randomize_word_list()
        self.current_word_list = []
        self.debug = 0
        self.clear_grid()
 
    def clear_grid(self): # initialize grid and fill with empty character
        self.grid = []
        for i in range(self.rows):
            ea_row = []
            for j in range(self.cols):
                ea_row.append(self.empty)
            self.grid.append(ea_row)
 
    def randomize_word_list(self): # also resets words and sorts by length
        temp_list = []
        for word in self.available_words:
            if isinstance(word, Word):
                temp_list.append(Word(word.word, word.clue))
            else:
                temp_list.append(Word(word[0], word[1]))
        random.shuffle(temp_list) # randomize word list
        temp_list.sort(key=lambda i: len(i.word), reverse=True) # sort by length
        self.available_words = temp_list
 
    def compute_crossword(self, time_permitted = 1.00, spins=2):
        time_permitted = float(time_permitted)
 
        count = 0
        copy = Crossword(self.cols, self.rows, self.empty, self.maxloops, self.available_words)
 
        start_full = float(time.time())
        while (float(time.time()) - start_full) < time_permitted or count == 0: # only run for x seconds
            self.debug += 1
            copy.current_word_list = []
            copy.clear_grid()
            copy.randomize_word_list()
            x = 0
            while x < spins: # spins; 2 seems to be plenty
                for word in copy.available_words:
                    if word not in copy.current_word_list:
                        copy.fit_and_add(word)
                x += 1

            if len(copy.current_word_list) > len(self.current_word_list):
                self.current_word_list = copy.current_word_list
                self.grid = copy.grid
            count += 1
        return

    def suggest_coord(self, word):
        count = 0
        coordlist = []
        glc = -1
        for given_letter in word.word: # cycle through letters in word
            glc += 1
            rowc = 0
            for row in self.grid: # cycle through rows
                rowc += 1
                colc = 0
                for cell in row: # cycle through  letters in rows
                    colc += 1
                    if given_letter == cell: # check match letter in word to letters in row
                        try: # suggest vertical placement 
                            if rowc - glc > 0: # make sure we're not suggesting a starting point off the grid
                                if ((rowc - glc) + word.length) <= self.rows: # make sure word doesn't go off of grid
                                    coordlist.append([colc, rowc - glc, 1, colc + (rowc - glc), 0])
                        except: pass
                        try: # suggest horizontal placement 
                            if colc - glc > 0: # make sure we're not suggesting a starting point off the grid
                                if ((colc - glc) + word.length) <= self.cols: # make sure word doesn't go off of grid
                                    coordlist.append([colc - glc, rowc, 0, rowc + (colc - glc), 0])
                        except: pass

        new_coordlist = self.sort_coordlist(coordlist, word)
        #print new_coordlist
        return new_coordlist
 
    def sort_coordlist(self, coordlist, word): # give each coordinate a score, then sort
        new_coordlist = []
        for coord in coordlist:
            col, row, vertical = coord[0], coord[1], coord[2]
            coord[4] = self.check_fit_score(col, row, vertical, word) # checking scores
            if coord[4]: # 0 scores are filtered
                new_coordlist.append(coord)
        random.shuffle(new_coordlist) # randomize coord list; why not?
        new_coordlist.sort(key=lambda i: i[4], reverse=True) # put the best scores first
        return new_coordlist
 
    def fit_and_add(self, word): # doesn't really check fit except for the first word; otherwise just adds if score is good
        fit = False
        count = 0
        coordlist = self.suggest_coord(word)
 
        while not fit and count < self.maxloops:
 
            if len(self.current_word_list) == 0: # this is the first word: the seed
                # top left seed of longest word yields best results (maybe override)
                vertical, col, row = random.randrange(0, 2), 1, 1
                ''' 
                # optional center seed method, slower and less keyword placement
                if vertical:
                    col = int(round((self.cols + 1)/2, 0))
                    row = int(round((self.rows + 1)/2, 0)) - int(round((word.length + 1)/2, 0))
                else:
                    col = int(round((self.cols + 1)/2, 0)) - int(round((word.length + 1)/2, 0))
                    row = int(round((self.rows + 1)/2, 0))
                # completely random seed method
                col = random.randrange(1, self.cols + 1)
                row = random.randrange(1, self.rows + 1)
                '''
 
                if self.check_fit_score(col, row, vertical, word): 
                    fit = True
                    self.set_word(col, row, vertical, word, force=True)
            else: # a subsquent words have scores calculated
                try: 
                    col, row, vertical = coordlist[count][0], coordlist[count][1], coordlist[count][2]
                except IndexError: return # no more cordinates, stop trying to fit
 
                if coordlist[count][4]: # already filtered these out, but double check
                    fit = True 
                    self.set_word(col, row, vertical, word, force=True)
 
            count += 1
        return
 
    def check_fit_score(self, col, row, vertical, word):
        '''
        And return score (0 signifies no fit). 1 means a fit, 2+ means a cross.
 
        The more crosses the better.
        '''
        if col < 1 or row < 1:
            return 0
 
        count, score = 1, 1 # give score a standard value of 1, will override with 0 if collisions detected
        for letter in word.word:            
            try:
                active_cell = self.get_cell(col, row)
            except IndexError:
                return 0
 
            if active_cell == self.empty or active_cell == letter:
                pass
            else:
                return 0
 
            if active_cell == letter:
                score += 1
 
            if vertical:
                # check surroundings
                if active_cell != letter: # don't check surroundings if cross point
                    if not self.check_if_cell_clear(col+1, row): # check right cell
                        return 0
 
                    if not self.check_if_cell_clear(col-1, row): # check left cell
                        return 0
 
                if count == 1: # check top cell only on first letter
                    if not self.check_if_cell_clear(col, row-1):
                        return 0
 
                if count == len(word.word): # check bottom cell only on last letter
                    if not self.check_if_cell_clear(col, row+1): 
                        return 0
            else: # else horizontal
                # check surroundings
                if active_cell != letter: # don't check surroundings if cross point
                    if not self.check_if_cell_clear(col, row-1): # check top cell
                        return 0
 
                    if not self.check_if_cell_clear(col, row+1): # check bottom cell
                        return 0
 
                if count == 1: # check left cell only on first letter
                    if not self.check_if_cell_clear(col-1, row):
                        return 0
 
                if count == len(word.word): # check right cell only on last letter
                    if not self.check_if_cell_clear(col+1, row):
                        return 0
 
 
            if vertical: # progress to next letter and position
                row += 1
            else: # else horizontal
                col += 1
 
            count += 1
 
        return score
 
    def set_word(self, col, row, vertical, word, force=False): # also adds word to word list
        if force:
            word.col = col
            word.row = row
            word.vertical = vertical
            self.current_word_list.append(word)
 
            for letter in word.word:
                self.set_cell(col, row, letter)
                if vertical:
                    row += 1
                else:
                    col += 1
        return
 
    def set_cell(self, col, row, value):
        self.grid[row-1][col-1] = value
 
    def get_cell(self, col, row):
        return self.grid[row-1][col-1]
 
    def check_if_cell_clear(self, col, row):
        try:
            cell = self.get_cell(col, row)
            if cell == self.empty: 
                return True
        except IndexError:
            pass
        return False
 
    def order_number_words(self): # orders words and applies numbering system to them
        self.current_word_list.sort(key=lambda i: (i.col + i.row))
        count, icount = 1, 1
        for word in self.current_word_list:
            word.number = count
            if icount < len(self.current_word_list):
                if word.col == self.current_word_list[icount].col and word.row == self.current_word_list[icount].row:
                    pass
                else:
                    count += 1
            icount += 1

    def solution(self): # return solution grid
        outStr = ""
        for r in range(self.rows):
            for c in self.grid[r]:
                outStr += '%s ' % c
            outStr += '\n'
        fo = open("foo.txt", "a")
        fo.write(''.join(str(e) for e in self.grid))
        # Close opend file
        fo.close()
        return outStr
 
    def display(self, order=True): # return (and order/number wordlist) the grid minus the words adding the numbers
        outStr = ""
        if order:
            self.order_number_words()
 
        copy = self
 
        for word in self.current_word_list:
            copy.set_cell(word.col, word.row, word.number)
 
        for r in range(copy.rows):
            for c in copy.grid[r]:
                outStr += '%s ' % c
            outStr += '\n'
 
        outStr = re.sub(r'[a-z]', ' ', outStr)
        return outStr
 
    def word_bank(self): 
        outStr = ''
        temp_list = duplicate(self.current_word_list)
        random.shuffle(temp_list) # randomize word list
        for word in temp_list:
            outStr += '%s\n' % word.word
        fo = open("foo.txt", "a")
        fo.write(outStr)
        # Close opend file
        fo.close()
        return outStr
 
    def legend(self): # must order first
        outStr = ''
        for word in self.current_word_list:
            outStr += '%d. (%d,%d) %s: %s\n' % (word.number, word.col, word.row, word.down_across(), word.clue )
        fo = open("foo.txt", "a")
        fo.write(outStr)
        # Close opend file
        fo.close()
        return outStr
 
class Word(object):
    def __init__(self, word=None, clue=None):
        self.word = re.sub(r'\s', '', word.upper())
        self.clue = clue
        self.length = len(self.word)
        # the below are set when placed on board
        self.row = None
        self.col = None
        self.vertical = None
        self.number = None
 
    def down_across(self): # return down or across
        if self.vertical: 
            return 'down'
        else: 
            return 'across'
 
    def __repr__(self):
        return self.word
 
### end class, start execution
easy = ['sorry', 'A word used to indicate an apology'], \
	['ice', 'Water in its solid state'], \
	['hello', 'Spoken when meeting someone'], \
	['cower', 'To hide when frightened.'], \
	['happy', 'A synonym to joy'], \
	['confusion', 'A state of not understanding and having difficulty understanding'], \
	['healthy', 'An adjective used to show the body is in a good state'], \
	['purple', 'A mixture of blue and red together'], \
	['approach', 'To come closer to someone or something'], \
	['tamper', 'To manipulate or meddle with something'], \
	['foreign', 'An indication implying not coming from the country'], \
	['capsule', 'A tiny container']
	
medium = ['subjugate', 'To bring under domination or control, especially by conquest'], \
	['malnourish', 'A state indicating a lack of nutrients'], \
	['abhor', 'Regard with disgust and hate'], \
	['folly', 'Foolishness'], \
	['vibrant', 'Full of energy and life'], \
	['resonant', 'Reverberate'], \
	['abyss', 'A vast chasm'], \
	['linger', 'To stay around longer than necessary'], \
	['sycophant', 'An individual that acts obsequiously towards someone important in order to gain advantage'], \
	['tyrant', 'A cruel and oppressive ruler'], \
	['tangible', 'Perceptible by touch']

hard = ['REIGN', 'To hold and exercise sovereign power'], \
	['REIMBURSE', 'To pay back as an equivalent of what has been expended'], \
	['REIN', 'A step attached to the bit for controlling a horse or other draft-animal'], \
	['REINSTATE', 'To restore to a former state, station, or authority'], \
	['REITERATE', 'To say or do again and again'], \
	['REJOIN', 'To reunite after separation'], \
	['abrogate', 'Revoke formally'], \
	['compunction', 'A feeling of deep regret, usually for some misdeed'], \
	['dogmatic', 'Pertaining to a code of beliefs accepted as authoritative'], \
	['empirical', 'Derived from experiment and observation rather than theory'], \
	['inveterate', 'Habitual'], \
	['maudlin', 'Effusively or insincerely emotional'], \
	['noxious', 'Injurious to physical or mental health'], \
	['tome', 'A large, scholarly book']
	
got = ['BOLTON', '''"Our blades are sharp."'''], \
    ['DAENERYS', 'The Mother of Dragons.'], \
    ['FLOWERS', 'The surname given to bastards of The Reach.'], \
    ['GREGOR', 'First name of The Mountain.'], \
    ['RENLY', 'The first name of the first husband of Margarey Tyrell.'], \
    ['ELLARIA', 'The paramour of Oberyn Martell.'], \
    ['CASTAMERE', '''"And so he spoke, and so he spoke: that Lord of _________."'''], \
    ['DRAGONGLASS', 'The only material known to kill White Walkers.'], \
    ['VISERION', 'The most gentle of the three dragons.'], \
    ['RHAEGAR', '''Lyanna Stark's kidnapper.'''], \
    ['FORRESTER', '''"Iron from Ice."'''], \
    ['SHAE', 'The deceased lover of Tyrion Lannister.'], \
    ['OATHBREAKER', 'The title given to Jaime Lannister after assassinating the Mad King.'], \
    ['JON', 'The bastard son of Ned Stark.'], \
    ['JOJEN', 'The boy that assisted Bran with the Sight.'], \
    ['RAVEN', 'The creature Bran searched for to understand more about the Sight.'], \
    ['BAELISH', 'The house of Littlefinger.'], \
    ['DORNE', 'The only place where bastards are treated equally.'], \
    ['ARYA', 'The youngest daughter of the Starks.'], \
    ['REEK', 'The nickname given to Theon Greyjoy while held captive by Ramsay Bolton.']
 
# Choose which word list is wanted

choice = input("Enter Easy, Medium or Hard: ")

if choice == "Easy":
	word_list = easy

elif choice == "Medium":
	word_list = medium
 
else:
	word_list = hard

a = Crossword(13, 13, '-', 5000, word_list)
a.compute_crossword(2)
print(a.word_bank())
print(a.solution())
print(a.display())
print(a.legend())
print(len(a.current_word_list), 'out of', len(word_list))
