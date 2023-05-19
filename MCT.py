import numpy as np
import copy


class MCNode:
    def __init__(self, state, parent=None):
        # Initialize the Monte Carlo node with the given state and parent
        self.state = state
        self.parent = parent
        self.children = []
        # Initialize the children list to an empty list
        self.visits = 1
        # The number of times this node has been visited
        self.wins = 0
        # The number of times this node has resulted in a win

        # Determine whose turn it is based on the parent node, or initialize to 1 if no parent
        if parent is None:
            self.turn = 1
        else:
            self.turn = parent.turn * -1

    def add_child(self, child_state):
        # Create a new child node with the given child state and add it to the children list
        child_node = MCNode(child_state, parent=self)
        self.children.append(child_node)
        return child_node

    def fully_expanded(self):
        # Check if all legal moves from this node have already been explored
        moves = self.state.get_legal_moves()
        for move in moves:
            explored = False
            for child in self.children:
                # check every child
                if child.state.currentGuess == move:
                    explored = True
                    break
            if not explored:
                # false if one instance is found
                return False
        # true if no instance is unexplored
        return True



class MCstate:
    def __init__(self, size=3, availableWords=None, prevFeedback=None, currentGuess=""):
        self.prevFeedback = prevFeedback
        # feedback from previous move
        self.currentGuess = currentGuess
        # current move
        if availableWords is None:
            self.availableWords = self.populate(size)
            # set of possible words
        else:
            self.availableWords = availableWords

    def populate(self, size):
        word_set = set()
        # create empty set for words
        file = open("{0}a.txt".format(str(size)), "r")
        # open file containing words
        line = file.readline().strip()
        while True:
            if line == "":
                break
            word_set.add(line)
            # add word to set
            line = file.readline().strip()
        file.close()
        # close file

        return word_set
        # return set of words

    def get_legal_moves(self):
        return copy.deepcopy(self.availableWords)
        # return deep copy of set of possible words

    def make_move(self, move, correctWord):
        feedback = comparison(correctWord=correctWord, guess=move)
        # compare current move to correct word and get feedback
        self.currentGuess = move
        # set current move to the given move
        return MCstate(size=len(move), availableWords=self.get_legal_moves(), prevFeedback=feedback, currentGuess=move)
        # create new state object with updated parameters

    def is_terminal(self, correctWord):
        if self.currentGuess == correctWord:
            return True
            # if current move is correct word, return True
        return False
        # otherwise, return False

    def make_random_move(self, correctWord):
        words = list(self.get_legal_moves())
        # get list of possible words
        try:
            return self.make_move(move=np.random.choice(words), correctWord=correctWord)
            # choose a random word from list and make the move
        except:
            print("No moves for the random move maker")
            raise ValueError
            # This error should never be possible


class MonteCarloTree:
    def __init__(self, wordsize, explorationConstant=np.sqrt(2)):
        self.explorationConstant = explorationConstant
        self.root = MCNode(state=MCstate(size=wordsize))
        self.correctWord = ""
        self.wordsize = wordsize

    def calculate_ucb_score(self, node):

        # Calculate the exploitation term
        exploitation_term = node.wins / node.visits

        # Calculate the exploration term
        exploration_term = self.explorationConstant * np.sqrt(np.log(node.parent.visits) / node.visits)

        # Add the exploitation and exploration terms together and return the result, which represents the
        # UCB score for the given node
        return exploitation_term + exploration_term

    def selection(self, node):
        # Initialize previous maximum UCB score as negative infinity and chosen child as an empty list
        prevMax = -np.inf
        chosenChild = []

        try:
            # Loop through all the children of the given node
            for child in node.children:
                # Calculate the UCB score for the child and compare it with the previous maximum UCB score
                if self.calculate_ucb_score(child) > prevMax:
                    # If the UCB score is greater than the previous maximum, update the chosen child and previous maximum
                    chosenChild = [child]
                    prevMax = self.calculate_ucb_score(child)
                elif self.calculate_ucb_score(child) == prevMax:
                    # If the UCB score is equal to the previous maximum, append the child to the list of chosen children
                    chosenChild.append(child)
                    prevMax = self.calculate_ucb_score(child)
        except:
            # If any error occurs during the selection process, raise a ValueError
            # this was used for debugging
            print("selection failed")
            raise ValueError

        # If there are more than one chosen child, randomly choose one of them
        if len(chosenChild) > 1:
            chosenChild = np.random.choice(chosenChild)
        elif len(chosenChild) == 1:
            # If there's only one chosen child, set it as the chosen child
            chosenChild = chosenChild[0]
        else:
            # If there are no chosen children, return the original node
            return node

        # If the chosen node is fully expanded, recurse the selection process on it to expand recursively
        if node.fully_expanded():
            self.stateAdjust(chosenChild,node.state.availableWords)
            return self.selection(chosenChild)
        else:
            # If the current node is not fully expanded, return the node so that it will be
            return node

    def expansion(self, node):
        # Get the legal moves from the node's state
        legal_moves = node.state.get_legal_moves()

        # Create a list of unexplored moves
        unexplored_moves = []
        for move in legal_moves:
            # Check if the move has already been explored
            explored = False
            children = node.children
            for child in children:
                guess = child.state.currentGuess
                if guess == move:
                    explored = True
                    break
            # Add the move to the list of unexplored moves if it hasn't been explored yet
            if not explored:
                unexplored_moves.append(move)

        # If there are unexplored moves, choose one at random and create a child node
        if unexplored_moves:
            # Choose a move at random
            moveToMake = np.random.choice(unexplored_moves)

            # Make a copy of the node's state
            state = copy.deepcopy(node.state)

            # Make the chosen move and update the available words
            childstate = state.make_move(move=moveToMake, correctWord=self.correctWord)
            feedback = comparison(correctWord=self.correctWord, guess=moveToMake)
            childstate.availableWords = trim_availableWords(words=childstate.availableWords, feedback=feedback)

            # Add the child node and return it
            return node.add_child(childstate)
        else:
            # Raise a ValueError if there are no unexplored moves
            # this should not be possible, the selection phase should guarantee that
            print("expansion has no unexplored moves")
            raise ValueError

    def simulation(self, node):
        # Get the turn and copy the state from the given node
        turn = node.turn
        state = copy.deepcopy(node.state)

        # Initialize a loop counter to detect infinite loops
        loopCounter = 0

        # Loop until the state is terminal
        while not state.is_terminal(correctWord=self.correctWord):
            loopCounter += 1

            # Check for infinite loops and raise an error if necessary
            if loopCounter > 1000:
                # this should also never happen, but it happends if the correct word cannot be found.
                # if this error occurs the word filtering process is broken
                raise TimeoutError

            # Make a random move and update the available words for the next depth
            state = state.make_random_move(correctWord=self.correctWord)
            state.availableWords = trim_availableWords(words=state.availableWords, feedback=state.prevFeedback)

            # Switch the turn
            turn = turn * -1

        # Return the final turn
        return turn

    def backpropagation(self, node, result):
        # recursively send the results up the tree from the leaf node
        if not (node is None):
            node.wins += result
            node.visits += 1
            # change the result value according to the depth
            return self.backpropagation(node.parent, result * -1)

    def get_best_move(self, node):
        # Initialize variables to store the best results
        best = -np.inf
        best_child = ""

        # Loop over the children of the node
        for index, child in enumerate(node.children):
            # the most visited move is determined to be the best move
            if child.visits > best:
                best_child = child
                best = child.visits

        # and pull out the best child of that node
        return best_child

    def stateAdjust(self, node, parentWords):
        # I get feedback from the comparison function, which takes the guess and the correct word
        feedback = comparison(correctWord=self.correctWord, guess=node.state.currentGuess)
        # I note that feedback, this is great to have when debugging
        node.state.prevFeedback = feedback
        # I remove most words that are irrelevant to us, with the feedback as the guide
        node.state.availableWords = trim_availableWords(words=parentWords, feedback=feedback)

def comparison(correctWord, guess):
    # algorithm to validate words according to the guess and correct word
    guessResult = [""] * len(guess)
    feedbackString = ["-"] * len(correctWord)
    # I assume everything is wrong to begin with

    wordDict = {}
    # this is nice as a dict when we have multiple letters and they are not all completely correct

    # first run to find Correct letters
    for index, letter in enumerate(correctWord):
        if letter == guess[index]:
            # then I correct my assumption with each letter I find
            feedbackString[index] = "C"
        else:
            # I store the leftovers from the correct word
            guessResult[index] = guess[index]
            try:
                wordDict[letter] += 1
            except KeyError:
                wordDict[letter] = 1

    # here I go over the leftovers, and remove them each time I find one in the dict
    # this is the assignment of c
    for index, letter in enumerate(guessResult):
        if letter == "":
            pass
        else:
            if letter in wordDict:
                feedbackString[index] = "c"
                if wordDict[letter] <= 1:
                    # I remove the character from the dict if I find anything
                    wordDict.pop(letter)
                else:
                    # If multiples of the same letter I retract 1 from that dict entry
                    wordDict[letter] -= 1
    # returns the feedback, which has the score and the guess that gave me this score
    return [''.join(feedbackString), guess]


def trim_availableWords(words, feedback):
    # Initialize two sets to hold good, and great characters
    goodChars = set()
    greatChars = set()

    # Loop through each character and its index in the feedback string
    for index, char in enumerate(feedback[1]):
        # If the corresponding character in feedback[0] is 'C', add the character to greatChars
        if feedback[0][index] == "C":
            greatChars.add(char)
        # If the corresponding character in feedback[0] is 'c', add the character to goodChars
        elif feedback[0][index] == "c":
            goodChars.add(char)

    # Initialize a list to hold filtered words
    filteredWords = []

    # Loop through each word in the input list
    for word in words:
        # Initialize a flag to indicate whether the word should be included
        include = True

        # Loop through each character and its index in the feedback string
        for index, char in enumerate(feedback[1]):
            # If the corresponding character in feedback[0] is 'C'
            if feedback[0][index] == "C":
                # all possible words should have this character in this position
                if char != word[index]:
                    include = False
                    break

            # If the corresponding character in feedback[0] is 'c'
            if feedback[0][index] == "c":
                # this character should be present in all the words somewhere
                if char not in word:
                    include = False
                    break

            # If the corresponding character in feedback[0] is '-'
            if feedback[0][index] == "-":
                # this character should not appear in the word, unless it's already been seen as "c" or "C"
                if word[index] == char and char not in goodChars and char not in greatChars:
                    include = False
                    break

        # If the word meets the filtering criteria, add it to the list of filtered words
        if include:
            filteredWords.append(word)

    # Return the list of filtered words
    return filteredWords