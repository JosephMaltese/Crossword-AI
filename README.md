# Crossword-AI
An AI that solves crossword puzzles, given a particular puzzle structure and word bank for the puzzle. The AI uses an inference-based backtracking algorithm to test possible word choices efficiently. After each move is made within the backtracking function, the ac3 algorithm is used to draw inferences based on the new state of the board. This project was an assignment for the Harvard CS50 AI course.

To run this file, use
python generate.py data/structure1.txt data/words1.txt       --(with whichever structure and words file you would like).
Optionally, if you would like a visual output of the solved board, use
python generate.py data/structure1.txt data/words1.txt output.png


![Preview](https://raw.githubusercontent.com/JosephMaltese/Crossword-AI/master/output.png)
