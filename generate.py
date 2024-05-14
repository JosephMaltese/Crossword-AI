import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable in self.domains:
            words_to_remove = []
            for word in self.domains[variable]:
                if len(word) != variable.length:
                    words_to_remove.append(word)
            for word in words_to_remove:
                self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        overlap = self.crossword.overlaps[x,y]
        revisionMade = False
        words_to_remove = []
        for word1 in self.domains[x]:
            found = False
            for word2 in self.domains[y]:
                if word2 == word1:
                    continue
                if overlap == None:
                    found = True
                    break
                else:
                    if word1[overlap[0]] == word2[overlap[1]]:
                        found = True
                        break
            if not found:
                words_to_remove.append(word1)
                # self.domains[x].remove(word1)
                revisionMade = True

        for word in words_to_remove:
            self.domains[x].remove(word)

        return revisionMade


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            arcs = []
            for var1 in self.domains:
                for var2 in self.domains:
                    if var1 != var2 and self.crossword.overlaps[var1, var2] != None:
                        arcs.append((var1, var2))

        while len(arcs) != 0:
            currentArc = arcs[0]
            arcs = arcs[1:]

            x = currentArc[0]
            y = currentArc[1]
            revised = self.revise(x, y)
            if len(self.domains[x]) == 0:
                return False
            if revised:
                neighbours = self.crossword.neighbors(x)
                for neighbour in neighbours:
                    if neighbour != y:
                        arcs.append((neighbour, x))

        return True



    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.crossword.variables:
            if var not in assignment:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Check uniqueness
        for key1, val1 in assignment.items():
            for key2, val2 in assignment.items():
                if key1 != key2 and val1 == val2:
                    return False
            # Also check that each value is the correct length
            if len(val1) != key1.length: #or len(val2) != key2.length
                return False

            # Also check for conflicts with neighbours
            neighbours = self.crossword.neighbors(key1)
            for neighbour in neighbours:
                if neighbour in assignment:
                    overlap = self.crossword.overlaps[key1, neighbour]
                    if val1[overlap[0]] != assignment[neighbour][overlap[1]]:
                        return False

        return True





    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        options = self.domains[var]
        neighbours = self.crossword.neighbors(var)

        optionsAndVals = {}

        for option in options:
            n = 0
            for neighbour in neighbours:
                if neighbour in assignment:
                    continue
                intersection = self.crossword.overlaps[var, neighbour]
                if option in self.domains[neighbour]:
                    n+=1
                elif intersection != None:
                    for word in self.domains[neighbour]:
                        if option[intersection[0]] != word[intersection[1]]:
                            n+=1
            optionsAndVals[option] = n

        sortedOptions = sorted(optionsAndVals.items(), key=lambda x:x[1])
        sortedList = []
        for element in sortedOptions:
            sortedList.append(element[0])

        return sortedList




    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        options = []

        for variable in self.domains:
            if variable not in assignment:
                options.append(variable)


        first_option = options[0]
        min_domain = first_option
        for i in range(1, len(options)):
            option = options[i]
            if len(self.domains[option]) < len(self.domains[min_domain]):
                min_domain = option
        lowest_domains = []
        for option in options:
            if len(self.domains[option]) == len(self.domains[min_domain]):
                lowest_domains.append(option)
        if len(lowest_domains) == 1:
            return lowest_domains[0]

        first_option_degree = lowest_domains[0]
        highest_degree = first_option_degree

        for i in range(1,len(lowest_domains)):
            current = lowest_domains[i]
            if len(self.crossword.neighbors(current)) > len(self.crossword.neighbors(highest_degree)):
                highest_degree = current
        highest_degrees = []
        for current in lowest_domains:
            if len(self.crossword.neighbors(current)) == len(self.crossword.neighbors(highest_degree)):
                highest_degrees.append(current)

        return highest_degrees[0]



    # def backtrack(self, assignment):
    #     """
    #     Using Backtracking Search, take as input a partial assignment for the
    #     crossword and return a complete assignment if possible to do so.
    #
    #     `assignment` is a mapping from variables (keys) to words (values).
    #
    #     If no assignment is possible, return None.
    #     """
    #     if self.assignment_complete(assignment):
    #         return assignment
    #
    #     currentVariable = self.select_unassigned_variable(assignment)
    #     neighbours = self.crossword.neighbors(currentVariable)
    #
    #     for value in self.order_domain_values(currentVariable, assignment):
    #         already_in_assignment = False
    #         for key in assignment:
    #             if assignment[key] == value:
    #                 already_in_assignment = True
    #         if len(value) == currentVariable.length and not already_in_assignment:
    #             valid = True
    #             for neighbour in neighbours:
    #                 if neighbour in assignment:
    #                     intersect = self.crossword.overlaps[currentVariable, neighbour]
    #                     if value[intersect[0]] != assignment[neighbour][intersect[1]]:
    #                         valid = False
    #             if valid:
    #                 assignment[currentVariable] = value
    #
    #                 result = self.backtrack(assignment)
    #                 if result != None:
    #                     return result
    #                 else:
    #                     del assignment[currentVariable]
    #     return None



    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment

        currentVariable = self.select_unassigned_variable(assignment)
        neighbours = self.crossword.neighbors(currentVariable)

        arcs = [(neighbour, currentVariable) for neighbour in neighbours if neighbour not in assignment]
        if not self.ac3(arcs):
            return None

        for value in self.order_domain_values(currentVariable, assignment):
            already_in_assignment = False
            for key in assignment:
                if assignment[key] == value:
                    already_in_assignment = True
            if len(value) == currentVariable.length and not already_in_assignment:
                valid = True
                for neighbour in neighbours:
                    if neighbour in assignment:
                        intersect = self.crossword.overlaps[currentVariable, neighbour]
                        if value[intersect[0]] != assignment[neighbour][intersect[1]]:
                            valid = False
                if valid:
                    assignment[currentVariable] = value

                    result = self.backtrack(assignment)
                    if result != None:
                        return result
                    else:
                        del assignment[currentVariable]
        return None







def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()