#!/usr/bin/env python3

import re
import os
import sys
import tty
import json
import time
import queue
import random
import logging
import termios
import threading
from rubik.cube import Cube
from argparse import ArgumentParser, Action

log = None

##
#  Utility class to handle different ways of formatting the verbosity argument.
#  All of these will set the logging level to 'verbose':
#    -v 3
#    -vvv
#    -v -v -v
##
class VAction(Action):
    def __init__(self, option_strings, dest, nargs=None, const=None,
            default=None, type=None, choices=None, required=False, help=None,
            metavar=None):
        super(VAction, self).__init__(option_strings, dest, nargs, const,
                default, type, choices, required, help, metavar)
        self.values = 0
    def __call__(self, parser, args, values, option_string=None):
        if values is None:
            self.values += 1
        else:
            try:
                self.values = int(values)
            except ValueError:
                self.values = values.count('v')+1
            setattr(args, self.dest, self.values)

##
#  Initialize logging and return the logger object. Set verbosity according to
#  the arguments passed to the script.
##
def init_logging(args = None):
    global log
    log_level = logging.CRITICAL
    if args and args.verbosity is not None:
        if args.verbosity == 1:
            log_level = logging.WARNING
        elif args.verbosity == 2:
            log_level = logging.INFO
        elif args.verbosity == 3:
            log_level = logging.DEBUG

    formatter = logging.Formatter(fmt='%(levelname)s - %(msg)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    logger.addHandler(handler)

    logger.debug('Logging initialized')
    return logger

##
#  Represents a series of steps to be applied to the cube. Includes methods to
#  apply both the pattern and its inverse.
##
class Sequence:
    initial = "OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR"
    # name: The name of the Sequence (e.g. 'Ra')
    # fwd:  The steps to take when applying the sequence (e.g. 'R U Ri ...').
    # rev:  The steps to take when undoing the sequence. These can be derived by
    #       reversing the order of 'fwd', then inverting each step.
    # fmt:  The string to display when rendering the sequence. Unlike 'fwd' and
    #       'rev', this field has no formatting restrictions.
    #
    # NOTE: 'fwd' and 'rev' must be formatted in the way the rubik-cube library
    # expects. This includes changing all "_'" to "_i", changing all "_2" to
    # "_ _", and removing all groupings (e.g. "[R U R']" -> "R U R'")
    def __init__(self, name, fwd, rev, fmt):
        self.name = name
        self.fwd = fwd
        self.rev = rev
        self.fmt = fmt

        self.fwd_diff = self.gen_diff(self.fwd)
        log.debug(f"Generated fwd_diff: {''.join([self.initial[i] for i in self.fwd_diff])}")
        self.rev_diff = self.gen_diff(self.rev)
        log.debug(f"Generated rev_diff: {''.join([self.initial[i] for i in self.rev_diff])}")

    # Apply all steps to a solved cube, then reverse them and make sure the
    # cube returns to its initial state.
    def test(self):
        if not (self.fwd and self.rev):
            return False

        c = Cube(self.initial)
        c.sequence(self.fwd)
        c.sequence(self.rev)
        return (c.flat_str() == self.initial)

    @classmethod
    def gen_diff(cls, pattern):
        # Generate a diff string for each direction and store it
        SOLVED_CUBE_STR = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01"
        cube = Cube(SOLVED_CUBE_STR)
        s1 = cube.flat_str()
        cube.sequence(pattern)
        s2 = cube.flat_str()
        return [ s1.index(s2[i]) for i in range(len(s1)) ]

    # Apply all steps and return the updated cube.
    def apply(self, cube):
        cube.sequence(self.fwd)
        return cube

    # Apply the reverse steps to under an 'apply' operation
    def undo(self, cube):
        cube.sequence(self.rev)
        return cube

    # Derive the 'family' based on the Sequence's name. Example:
    #  'Ra' -> 'R'
    @property
    def family(self):
        return self.name[0]

    # Return the formatted list of steps for this sequence.
    def __str__(self):
        return self.fmt
    
    def apply_str(self, cube):
        return "".join([cube[self.fwd_diff[i]] for i in range(len(cube)) ])

    def undo_str(self, cube):
        return "".join([cube[self.rev_diff[i]] for i in range(len(cube)) ])

def is_solved(cube):
    return re.match(r"^[O]{9}(YYY|GGG|BBB|WWW){12}[R]{9}$", cube)

##
#  Recursively append patterns and check to see if the cube is solved. If it is,
#  return the pattern; otherwise, undo the step and move on to the next one.
#
#  The base case has been reached when the number of patterns in the chain
#  exceeds the maximum depth, which defaults to 4 (as defined in the script's
#  arguments).
#
#  If 'limit_one' is set (used in 'trainer' mode), stop after the first match is
#  found. This is currently bugged and continues through the rest of the first
#  loop.
##
def find_pattern(cube, pll, sequences, max_depth, pattern = None, all_patterns = None, limit_one=False):
    if limit_one:
        sequences = random.sample(sequences, len(sequences))

    if not pattern:
        pattern = []

    if not all_patterns:
        all_patterns = set()

    log.debug(f"Pattern: {', '.join(pattern):<18} - {cube}")
    prev_seq = []

    while len(sequences):
        # Get the next sequence and check to see if it has been used already
        seq = sequences.pop(0)
        if seq[0] not in [x[0] for x in pattern]:
            # Add the sequence to the current pattern and apply it to the cube
            cube = pll[seq].apply_str(cube)
            pattern.append(seq)
            # Check to see if we've reached a 'solved' state
            if is_solved(cube):
                log.info(f"Found pattern: {', '.join(pattern)}")
                all_patterns.add(" ".join(pattern))
                if limit_one:
                    return all_patterns
            # If not solved, check to see if we've reached the maximum depth
            elif len(pattern) < max_depth:
                all_patterns = all_patterns.union(
                                                    find_pattern(
                                                        cube,
                                                        pll,
                                                        sequences + prev_seq,
                                                        max_depth,
                                                        pattern,
                                                        all_patterns
                                                    )
                                                 )

                if limit_one and len(all_patterns):
                    return all_patterns

            # If we've reached this point, the cube is not solved and we haven't
            # reached the maximum depth. Undo the pattern and apply the next
            # one.
            pattern.remove(seq)
            cube = pll[seq].undo_str(cube)
        # Add the sequence to the list of attempted patterns
        prev_seq.append(seq)
    return all_patterns

def main():
    global log
    # Parse arguments and initialize logging
    parser = ArgumentParser(__name__, "Find permutations of PLL algorithms " +
                            "that return the cube to a solved state. If " +
                            "neither '--anki' or '--trainer' is specified, " +
                            "print all identified sequences and their " +
                            "patterns' respective steps.")
    parser.add_argument(action="store", nargs="*", dest="algorithms",
                        help="Override the list of algorithms that will be " +
                        "tested. If not specified, use all algorithms found " +
                        " in ./pll.json")
    parser.add_argument("-d", "--max-depth", default=4, help="Set maximum " +
                        "recursion depth (default: 4)")
    parser.add_argument("-a", "--anki", action="store_true", default=False,
                        help="Print all identified patterns in Anki's flash " +
                        "card format")
    parser.add_argument("-s", "--search", action="store", nargs="+",
                        help="Only include sequences that use at least one " +
                        "of the specified patterns")
    parser.add_argument("-t", "--trainer", action="store_true", default=False,
                        help="Pick a random sequence and present the steps " +
                        "one by one. Calculate time to solve each step, as " +
                        "well as total time and average time per step. " +
                        "Advance from one step to the next by pressing any " +
                        "key")
    parser.add_argument("-v", nargs="?", action=VAction, dest="verbosity",
                        help="Set log level. Accepted up to 3 times (e.g. " +
                        "-vvv)")
    args = parser.parse_args()
    log = init_logging(args)

    # Read available algorithms from './pll.json' and parse them into Sequence
    # objects.
    #
    # TODO: Make the file path user-controllable
    pll = {}
    with open('./pll.json') as f:
        _pll = json.load(f)
        for j in _pll["algorithms"]:
            pll[j["name"]] = Sequence(j["name"], j["fwd"], j["rev"], j["fmt"])
            if "variants" in j:
                for variant in j["variants"]:
                    v_fwd = variant
                    if len(v_fwd) == 1:
                        v_rev = f"{v_fwd}i"
                        v_fmt = v_fwd
                    elif len(v_fwd) == 2 and v_fwd[1] == "i":
                        v_rev = v_fwd[:-1]
                        v_fmt = f"{v_rev}'"
                    else:
                        continue

                    v = (v_fwd, v_rev, v_fmt)

                    pll[f"{v[2]}+{j['name']}"] = Sequence(
                        f"{v[2]}+{j['name']}",
                        f"{v[0]} {j['fwd']}",
                        f"{j['rev']} {v[1]}",
                        f"{v[2]} {j['fmt']}"
                    )
            log.debug(f"Parsed sequence {j['name']:<2}: {j['fmt']}")

## TODO:
#       "Na": "Z D Ri U R R Di R D Ui Ri U R R Di R Ui R",
#       "Nb": "Z Ui R Di R R U Ri D Ui R Di R R U Ri D Ri",
#       "Gc": "Ri Ri Ui E R Ui R U Ri U Ei R R Fi S Ri Si F",
#       "V":  "Ri U Ri Di Ei Ri Fi R R Ui Ri U Ri F R F",

    # Test all sequences
    for name,seq in pll.items():
        if not seq.test():
            log.error(f"Sequence {name} did not return cube to solved state")

    # Create a cube object and place it in the solved state
    cube = Cube(Sequence.initial)

    if args.algorithms:
        # If a list of algorithms was provided, drop any invalid entries
        sequences = list(set(args.algorithms).intersection(set(pll.keys())))
    else:
        # Otherwise, use the full set
        sequences = list(pll.keys())
    starting_sequences = set(sequences)

    limit_one = args.trainer
    patterns = find_pattern(cube.flat_str(), pll, sequences, int(args.max_depth), limit_one=limit_one)
    used_sequences = set()
    for p in patterns:
        pattern = p.split()
        # If a whitelist was provided, use it to filter the pattern list
        if (not args.search) or len(set(args.search).intersection(set(pattern))) > 0:
            if args.anki:
                # Print the raw list of matched sequences in Anki's flashcard
                # format ([front],[back],[tags])
                out = f"{' -> '.join(pattern[:-1])} -> _,"
                tags = []
                # Print each pattern wrapped in a <div>
                for a in pattern:
                    out = f"{out}<div>{str(pll[a])}</div>"
                    tags.append(a)
                out = f"{out},{' '.join(tags)}"
                print(out)
            elif not args.trainer:
                # Default case (not Anki or trainer mode): Print each sequence,
                # including both the list of patterns and their respective
                # steps.
                print(f"{' -> '.join(pattern)}")
                for a in pattern:
                    print(f"{a:<2} - {str(pll[a])}")
                print()
            used_sequences = used_sequences.union(set(pattern))

    # Print a list of all sequences that were not used at least once
    not_used = starting_sequences - used_sequences
    if len(not_used):
        log.debug(f"Not used: {', '.join(list(not_used))}")

    ##
    #  Whenever a key is pressed, add it to the queue to be handled inside the
    #  timer loop.
    ##
    def read_input(_queue):
        # Source: https://stackoverflow.com/questions/510357/21659588#21659588
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            # Handle arrow keys, which consist of 3-character ANSI escape
            # sequences. Source: https://stackoverflow.com/questions/22397289
            if ord(ch) == 27:
                ch = sys.stdin.read(2)
                _queue.put(' ')
            else:
                _queue.put(ch)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    ##
    #  Create a separate thread to listen for (blocking) keyboard input events
    ##
    def spawn_thread(_queue):
        thread = threading.Thread(target=read_input, args=(_queue,))
        thread.start()

    # 'Trainer' mode: select a random sequence from the identified list and step
    # through it. Each step is timed; advance steps by pressing any key. Press
    # ESC, Ctrl+C, or Ctrl+D to terminate, or advance through the last step.
    if args.trainer:
        if not len(patterns):
            log.critical("No patterns found; cannot continue")
            return 1

        pattern = random.choice(list(patterns)).split(" ")
        interval = 0.01
        elapsed = 0
        spacer = ""
        out = ""

        _queue = queue.Queue()
        spawn_thread(_queue)

        if len(pattern):
            last = False
            cont = True
            total = 0
            count = len(pattern)
            out = f"\x1bc{pattern.pop(0)}"

            while cont:
                try:
                    val = _queue.get(False)
                    if val:
                        if ord(val) in [ 3, 4, 27 ]:
                            total += elapsed
                            print(f"\nTotal: {total:.2f}s")
                            sys.exit(0)
                        try:
                            total += elapsed
                            out = f"{out} [{elapsed:.2f}s]"
                            # If the next step is the last one, mask it while
                            # the timer is running.
                            if len(pattern) == 1:
                                last_pattern = pattern.pop(0)
                                out = f"{out} -> _"
                            else:
                                out = f"{out} -> {pattern.pop(0)}"
                            elapsed = 0
                        except IndexError:
                            pass

                        if last:
                            cont = False
                        else:
                            # Spawn a new listener thread if there are more
                            # queued steps.
                            spawn_thread(_queue)

                        if not len(pattern):
                            last = True
                except queue.Empty:
                    pass

                sys.stdout.write("\r")
                sys.stdout.write(f"{out} [{elapsed:.2f}s]")
                sys.stdout.flush()
                time.sleep(interval)
                elapsed += interval

            sys.stdout.write("\r")
            sys.stdout.flush()
            print(out.replace(" -> _", f" -> {last_pattern}"))
            print(f"Total: {total:.2f}s")
            print(f"Avg:   {total/count:.2f}s")

if __name__ == "__main__":
    sys.exit(main())
