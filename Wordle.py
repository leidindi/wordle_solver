import random as rand
import pickle
import maps
import MCT
import time
import numpy as np


def clear():
    # A personal preference
    # clear the screen when playing a new game
    print("\n" * 90)


class GameEnvironment:
    def __init__(self):
        # these variables are for the environment
        self.CorrectMap = ""
        # correct map is the pool of all guesses, for all word sizes
        self.GuessMap = ""
        # guess map is the pool of all valid guesses, for all word sizes

        # the current word is the correct word at this time
        self.CurrentWord = ""

        # the user guess
        self.guess = ""

        # game handling variables
        self.command = ""
        self.guessprompts = ""

        # cycles is how often the game takes guesses each time
        self.cycles = 5
        # wordsize of the environment
        self.wordsize = 5

    def start_prompt(self):
        print("---------------  Wordle  ---------------")
        print("---------- Feedback explainer ----------")
        print("  Correct letter = C, wrong letter = -  ")
        print("  Right letter but a wrong position = c ")
        print("----------------------------------------")
        print("Would you like to change the settings? (n/y): ", end="")
        if input().lower() == "y":
            while True:
                try:
                    print("To change the guess amount enter the preferred number: ", end="")
                    self.cycles = int(input())

                    print("To change the word length choose one of the following")
                    print("available sizes :( 3 ,4 ,5 ,6 ,7 ): ", end="")
                    self.wordsize = int(input())
                    if self.wordsize < 3 or self.wordsize > 7:
                        # I want to have a sensible wordsize
                        raise ValueError
                    break
                except ValueError:
                    print("invalid input, please try again")

    def loadwords(self):
        # modularized process of inserting the data from the txt files
        self.CorrectMap = self.fillmap("{0}a.txt".format(str(self.wordsize)))
        self.GuessMap = self.fillmap("{0}v.txt".format(str(self.wordsize)))

    def resets(self):
        # resets the basic wordle game
        self.CurrentWord = ""
        self.guess = ""
        self.command = ""
        self.guessprompts = ""

    def getword(self, count=0):
        # retrieves a current word from the correct-word map
        tempindex = rand.randint(0, self.CorrectMap.capacity * 17) % self.CorrectMap.capacity
        tempbucket = self.CorrectMap.hash_table[tempindex]
        if tempbucket.size == 0:
            # I try again if I find an empty bucket
            self.getword()
            return
        tempitem = tempbucket.get_at_index(rand.randint(0, tempbucket.size - 1))

        self.CurrentWord = tempitem

    def getguess(self):
        # get a valid guess from the user
        while True:
            print("Take a guess: ", end="")
            guess = str(input()).lower()
            # I validate the guess
            if self.GuessMap.contains(guess) or self.CorrectMap.contains(guess):
                # check if it's in either of the maps
                self.guess = guess
                break
            else:
                print("Invalid guess, try another one")

    def fillmap(self, filename):
        # read from a txt and insert it into the map, and return the final map
        map = maps.HashMap()
        file = open(filename, "r")
        line = file.readline().strip()
        while True:
            if line == "":
                break
            map.insert(line, False)
            line = file.readline().strip()
        file.close()
        return map

    def train(self, wordsize=3, trainingLimit = 1000, trainingModulus = 50, wordCycleLimit = 10):
        # recieve the size of the words
        self.wordsize = wordsize

        # load all the words of that size
        self.loadwords()

        # define the depth of the game, its deep so the correct word must be found
        self.cycles = len(self.CorrectMap)

        def resettree():
            # to define the original empty tree
            # -------- Running this function erases the pickle files, and resets them to 0 --------
            tree = MCT.MonteCarloTree(wordsize=self.wordsize)
            # save the tree to a pickle file
            with open(f'MCT{self.wordsize}.pickle', 'wb') as f:
                pickle.dump(tree, f)
            print("Tree reset successful for size : ",tree.wordsize)
        # uncomment this line to reset the pickle files and therefore the tree
        # careful as this will erase the training you've done on the pickle file
        #return resettree()

        # retrieve the previous tree from the pickle file
        with open(f'MCT{self.wordsize}.pickle', 'rb') as f:
            tree = pickle.load(f)
            tree.explorationConstant = np.sqrt(100)

        # internal counter for how much training we've done
        trainer = 0
        print("---------- new run --------")
        while trainer < trainingLimit:
            self.resets()
            # resets the necessary variables

            self.getword()
            # get a new word for the game to work with

            tree.correctWord = self.CurrentWord
            # tell the tree what word that is

            # this cycle represents how many times we train on the same word, this for loop can be ran once or 100 times
            # if you'd like, it's up to you. If the correct word has been selected the later phases will be skipped and
            # a new word will be selected for the training

            for cycle in range(0, wordCycleLimit):
                # Selection phase
                # ---------------------------------------------------------------
                totaltime = 0
                if trainer % trainingModulus == 0:
                    start_time = time.perf_counter()

                # explained in the MCT.py file
                node = tree.selection(tree.root)

                def printStatus():
                    print(trainer)
                    print("All possible words: " + str(node.state.availableWords))
                    print("Current nodes Guess: " + str(node.state.currentGuess))
                    print("Previous feedback: " + str(node.state.prevFeedback))
                    print("Feedback: " + str(MCT.comparison(self.CurrentWord, node.state.currentGuess)))
                    print("Right word now: " + str(tree.correctWord))

                if node is None:
                    raise ValueError
                    # this should never occur, useful for debugging

                if not (node is tree.root) and False:
                    # only print this if your word-set is very small, useful for debugging and developing
                    printStatus()

                # I only want text output on every trainingModulus interval, much less spam, but nice to know
                if trainer % trainingModulus == 0:
                    # print execution time for each phase
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time
                    totaltime += execution_time
                    #print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
                    #print("Execution time for Selection:", execution_time, "seconds")

                # ---------------------------------------------------------------

                # ---------------------------------------------------------------
                # Expansion phase

                if trainer % trainingModulus == 0:
                    start_time = time.perf_counter()

                # explained in the MCT.py file
                node = tree.expansion(node)

                if trainer % trainingModulus == 0:
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time
                    totaltime += execution_time

                    #print("Execution time for Expansion:", execution_time, "seconds")

                if node.state.is_terminal(tree.correctWord):
                    # we found the correct word by accident
                    # propagate it through the tree, and break the loop to find a new word
                    tree.backpropagation(node, node.turn)
                    trainer += 1
                    break
                # ---------------------------------------------------------------

                # ---------------------------------------------------------------
                # Simulation phase

                if trainer % trainingModulus == 0:
                    start_time = time.perf_counter()

                if node.state.currentGuess == tree.correctWord:
                    # no simulation needed, as the correct word is found
                    simulation_result = node.turn
                    tree.backpropagation(node, simulation_result)
                    trainer += 1

                    if trainer % trainingModulus == 0:
                        end_time = time.perf_counter()
                        execution_time = end_time - start_time
                        totaltime += execution_time

                        #print("Execution time for Simulation:", execution_time, "seconds")
                    # break the loop to find a new word to train on
                    break
                else:

                    # explained in the MCT.py file
                    simulation_result = tree.simulation(node)

                    if trainer % trainingModulus == 0:
                        end_time = time.perf_counter()
                        execution_time = end_time - start_time
                        totaltime += execution_time
                        #print("Execution time for Simulation:", execution_time, "seconds")

                # ---------------------------------------------------------------

                # ---------------------------------------------------------------
                # Backpropagation phase
                if trainer % trainingModulus == 0:
                    start_time = time.perf_counter()

                # explained in the MCT.py file
                tree.backpropagation(node, simulation_result)

                if trainer % trainingModulus == 0:
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time

                    totaltime += execution_time
                    #print("Execution time for backpropagation:", execution_time, "seconds")
                    #print("Total execution time for all phases combined : ",end="")

                    print(totaltime)
                    #print("Training count this session : " + str(trainer))

                trainer += 1
                # ---------------------------------------------------------------
        # save the tree to a pickle file after this training round has completely finished

        print("---------- run is saving --------")
        with open(f'MCT{self.wordsize}.pickle', 'wb') as f:
            pickle.dump(tree, f)

    def play(self):
        # this function is just the wordle game and has nothing to do with the AI project directly, unless you want
        # to play wordle for fun, works for all sizes 3-7, enjoy!

        self.start_prompt()
        self.loadwords()
        while self.command != "y":
            self.resets()
            self.getword()
            if self.CurrentWord == "exitcommand":
                # in the rare case that we've already played all the words once
                break
            for cycle in range(self.cycles):
                # I only play like the original wordle,so whole word guesses only
                self.getguess()
                # save the results
                self.guessprompts += str(MCT.comparison(self.CurrentWord, self.guess)) + "\n"
                print(self.guessprompts)
                if self.guess == self.CurrentWord:
                    print("CORRECT ! WOOHOO!")
                    self.guessprompts += "\nThe word was " + self.CurrentWord + " and you won!"
                    break
                if cycle == self.cycles - 1:
                    print("You're out of guesses!")
                    self.guessprompts += "\nThe word was " + self.CurrentWord + " and you lost!"
                    print("The word was " + self.CurrentWord)
                    break
            print("What would you like to do?")
            print("To stop playing (y/n)")
            # print("To add to the answer pool (a)")
            # print("To add to the valid guesses pool (v)")
            self.command = str(input()).lower()
            if self.command == "a" or self.command == "v":
                print("enter (q) to quit ")
                newWord = ""
                while newWord != "q":
                    isok = True
                    file = open("{0}{1}.txt".format(str(self.wordsize), self.command), "a")
                    print("-- Enter the word you'd like to add: ", end="")
                    # I check on the words validity in reference to current settings
                    newWord = str(input()).lower()
                    if len(newWord) == self.wordsize:
                        for letter in newWord:
                            if not letter.isalnum():
                                isok = False
                    else:
                        isok = False
                    if isok:
                        # when im satisfied that the word fits the restraints.
                        file.write(newWord + "\n")
                        print("-- The word has been added")
                    else:
                        print("-- The word was not valid")
                    file.close()
            clear()

    def playVSbot(self):
        # this function is where the MCTS is tested against a human, as written in the report, it is no match to a human
        # for several reasons. That being said it runs and is playable, the tree just loses track in depth 3-4 and can't
        # compete at all if you go way out of the optimal path ( choose a word that is discarded most of the time).

        # a good way to throw off the MCTS is to guess the same word as it did previously, this is the worst possible
        # move to guess during the game, so the tree does has little data on what to do when you do it, and you will
        # therefore win all the games.

        self.start_prompt()
        self.loadwords()

        with open(f'MCT{self.wordsize}.pickle', 'rb') as f:
            # load the trained tree
            tree = pickle.load(f)

        # while user still wants to play
        while self.command != "y":

            node = tree.root
            self.resets()
            self.getword()

            for cycle in range(0, self.cycles+1):
                # User's guess
                self.getguess()
                self.guessprompts += str(MCT.comparison(self.CurrentWord, self.guess)) + "\n"
                print(self.guessprompts)

                if self.guess == self.CurrentWord:
                    print("YOUR GUESS WAS CORRECT ! WOOHOO!")
                    self.guessprompts += "\nThe word was indeed " + self.CurrentWord + "!"
                    break

                # this if sentence checks if we've turned the MCTS into a random generator that uses a list
                if not isinstance(node, list):
                    found = ""
                    for childs in node.children:
                        if childs.state.currentGuess == self.guess:
                            found = childs
                            break
                    if found == "":
                        # the client guess was not found, the tree is not extensive enough
                        # we have to randomize the remainder of the game, the tree needs to be bigger.
                        words = list(node.state.availableWords)
                        choice = np.random.choice(words)
                        node = [choice, words]
                    else:
                        # we found the user guess, and we keep on playing with the tree!
                        node = found

                # if the tree was not good enough and we need to randomize the game
                if isinstance(node, list):
                    # we know it if we've turned the node into a list
                    treeGuess = node[0]
                    # completely random choices
                    choice = np.random.choice(node[1])
                    node = [choice, node[1]]
                    print("Tree guess: " + treeGuess + ", it's random")
                else:
                    # if we still have nodes to work with.
                    node = tree.get_best_move(node)
                    treeGuess = node.state.currentGuess
                    print("Tree guess: " + treeGuess)

                # feedback from the treeguess
                self.guessprompts += str(MCT.comparison(self.CurrentWord, treeGuess)) + "\n"
                print(self.guessprompts.strip())

                if treeGuess == self.CurrentWord:
                    print("THE TREE GUESS WAS CORRECT ! YOU JUST LOST!")
                    self.guessprompts += "\nThe word was indeed " + self.CurrentWord + "!"
                    break

                if cycle >= np.floor(self.cycles/2):
                    print("You're out of guesses!")
                    print("The word was " + self.CurrentWord+ " and you both lost!")
                    break

            print("What would you like to do?")
            print("To stop playing (y/n)")
            self.command = str(input()).lower()
            clear()


if __name__ == "__main__":
    gameenv = GameEnvironment()
    while True:
        svar = input("Do you want : two-player(2), single-player(1), train(t) or quit(q)?")
        #svar = "t"
        if svar == "2":
            # 2 represents two-player game, which is just a regular wordle game
            gameenv.play()
        elif svar == "1":
            # represents a single-player game, where you fight against the MCTS
            gameenv.playVSbot()
        elif svar == "t":
            # here you can train the model on certain word size
            #print("To set the word length for the training choose one of the following")
            #print("available sizes :( 3 ,4 ,5 ,6 ,7 ): ", end="")

            #size = int(input())
            size = 5
            if size > 7 or size < 3:
                print("Incorrect input")
                raise ValueError
            else:
                gameenv.wordsize = size

            #svar = input("Do you want to do custom training (y/n)?")
            svar = "y"
            if svar == "y":
                #trainingLimit   = int(input("Input how many training runs you want: "))
                trainingLimit = 1000
                #trainingModulus = int(input("Input the how often you get prints: "))
                trainingModulus = 50
                #wordCycleLimit  = int(input("Input how many times each word should be trained on: "))
                wordCycleLimit = 50

                # training with user defined values
                gameenv.train(wordsize=size,trainingLimit=trainingLimit,trainingModulus=trainingModulus,wordCycleLimit=wordCycleLimit)
            else:
                # default training
                gameenv.train(wordsize=size)
        elif svar == "q":
            break
    print("Quitting.")
