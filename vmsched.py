"""vmsched.py: page replacement and processor scheduling, simulated.

Run it from a terminal in the folder that holds this file:
    python vmsched.py           (Windows)   or   python3 vmsched.py   (macOS / Linux)

Your work is marked with TODO. Everything else already works: run the file before you change
anything; each experiment that reaches an unwritten TODO says which one and the rest still run.
Every "random" number comes from a generator started with a fixed seed, so the whole output is
the same on every computer and every run.
"""

import random  # the seeded random-number generator that builds the reference strings and the workload
from collections import deque  # a queue with fast removal from the front: the ready queue of round robin

SEED = 2026  # the generator's starting point; the same seed gives the same "random" numbers everywhere
PAGES = 40  # Experiment 1: the process has 40 virtual pages, numbered 0 to 39
REF_LENGTH = 3000  # Experiment 1: each reference string holds 3,000 page references
MAX_FRAMES = 10  # Experiment 1: the fault table tries 1, 2, ..., 10 frames
BELADY_STRINGS = 20000  # Experiment 2: how many short random strings are tested for Belady's anomaly
BELADY_LENGTH = 30  # Experiment 2: references per short string
BELADY_PAGES = 6  # Experiment 2: pages per short string, numbered 0 to 5
NUM_PROCS = 600  # Experiment 4: processes in the random workload
MEAN_SERVICE = 5  # Experiment 4: average service time (time units of processor work) per process
MEAN_GAP = 5.5  # Experiment 4: average time between arrivals; 5 / 5.5 keeps the processor about 90% busy


class NotWrittenYet(Exception):  # a custom error the starter raises wherever a TODO has not been written yet
    pass  # it needs no extra behavior; its name and message say everything


# ---------------------------------------------------------------------------
# Reference strings: the order in which a process touches its pages
# ---------------------------------------------------------------------------
def locality_refs(rng, length, pages):  # a string with locality: the process works on a few pages for a while, then moves on
    refs = []  # the string being built
    while len(refs) < length:  # one phase per trip around this loop, until the string is long enough
        size = rng.randint(3, 6)  # this phase's working set holds 3 to 6 pages
        start = rng.randrange(pages - size + 1)  # it is a run of neighbouring pages, like one loop's code or one array
        working = list(range(start, start + size))  # the pages of this phase, e.g. [12, 13, 14, 15]
        for _ in range(rng.randint(50, 250)):  # the phase lasts 50 to 250 references
            if rng.random() < 0.9:  # 9 references in 10 stay inside the working set...
                refs.append(rng.choice(working))  # ...on one of its pages, picked at random
            else:  # ...and 1 in 10 strays anywhere (a global variable, a library call, the stack)
                refs.append(rng.randrange(pages))  # any page of the process
    return refs[:length]  # cut the last phase short so the string has exactly `length` references


def uniform_refs(rng, length, pages):  # a string with NO locality: every reference is equally likely to hit any page
    return [rng.randrange(pages) for _ in range(length)]  # one independent random page per reference


# ---------------------------------------------------------------------------
# Page replacement: each function returns how many page faults the string causes
# (a fault is counted every time the referenced page is not resident, including the first loads)
# ---------------------------------------------------------------------------
def fifo(refs, nframes):  # first in, first out: evict the page that has been in memory longest
    frames = []  # the resident pages, oldest first
    faults = 0  # faults so far
    for page in refs:  # one reference at a time, in order
        if page in frames:  # a hit: the page is already in a frame...
            continue  # ...and FIFO does nothing on a hit
        faults += 1  # a miss: page fault
        if len(frames) == nframes:  # every frame is taken...
            frames.pop(0)  # ...so evict the oldest page, at the front of the list
        frames.append(page)  # the new page is now the youngest, at the back
    return faults  # the total


def next_use(refs, i, page):  # when is `page` referenced next after position i? (used by OPT)
    try:  # list.index raises ValueError when the value does not occur
        return refs.index(page, i + 1)  # the position of its next reference
    except ValueError:  # it is never referenced again...
        return len(refs)  # ...which counts as farther away than any real reference


def opt(refs, nframes):  # optimal: evict the page whose next use lies farthest in the future (needs to know the future)
    frames = []  # the resident pages; list position = frame number
    faults = 0  # faults so far
    for i, page in enumerate(refs):  # i is the position of this reference in the string
        if page in frames:  # a hit
            continue  # nothing to do
        faults += 1  # a page fault
        if len(frames) < nframes:  # a frame is still empty...
            frames.append(page)  # ...so the page simply goes into it
            continue  # and this reference is done
        victim = max(frames, key=lambda p: next_use(refs, i, p))  # the farthest next use; on a tie max() keeps the lowest frame
        frames[frames.index(victim)] = page  # the new page takes the victim's frame
    return faults  # the total


def lru(refs, nframes):  # least recently used: evict the page that has gone unused for the longest time
    frames = []
    faults = 0
    for page in refs:
        if page in frames:
            frames.remove(page)
        else:
            faults += 1
            if len(frames) == nframes:
                frames.pop(0)
        frames.append(page)
    return faults


def clock(refs, nframes):  # the clock policy: FIFO order plus a use bit that gives a recently used page a second chance
    frames = [None] * nframes
    bits = [0] * nframes
    hand = faults = 0
    for page in refs:
        if page in frames:
            bits[frames.index(page)] = 1
            continue
        faults += 1
        while frames[hand] is not None and bits[hand] == 1:
            bits[hand] = 0
            hand = (hand + 1) % nframes
        frames[hand] = page
        bits[hand] = 1
        hand = (hand + 1) % nframes
    return faults


POLICIES = (("OPT", opt), ("FIFO", fifo), ("LRU", lru), ("CLOCK", clock))  # the replacement policies, in the order the tables print them


def experiment_faults():  # fault counts for 1 to 10 frames, on a string with locality and on a uniform random one
    print(f"Experiment 1: page faults for {REF_LENGTH:,} references to {PAGES} pages")  # a title
    rng = random.Random(SEED)  # a fresh generator, so this experiment's strings do not depend on the others
    strings = (("with locality", locality_refs(rng, REF_LENGTH, PAGES)), ("uniform random", uniform_refs(rng, REF_LENGTH, PAGES)))  # the two strings
    for label, refs in strings:  # one table per string
        print(f"  reference string {label}")  # which string this table is for
        print("    frames " + "".join(f"{n:>6}" for n in range(1, MAX_FRAMES + 1)))  # the header: 1 to 10 frames
        for name, policy in POLICIES:  # one row per policy
            counts = [policy(refs, n) for n in range(1, MAX_FRAMES + 1)]  # the faults for every frame count (an unwritten TODO stops here)
            print(f"    {name:<6} " + "".join(f"{c:>6}" for c in counts))  # the row


def anomaly(counts):  # does a fault list for 1, 2, 3, ... frames ever go UP when one frame is added?
    return any(more > fewer for fewer, more in zip(counts, counts[1:]))  # compare each count with the next one


def experiment_belady():  # how often does each policy show Belady's anomaly on short random strings?
    print(f"\nExperiment 2: Belady's anomaly in {BELADY_STRINGS:,} random strings ({BELADY_LENGTH} references, {BELADY_PAGES} pages)")  # a title
    rng = random.Random(SEED + 1)  # a separate generator (seed 2027) for this experiment
    tests = [uniform_refs(rng, BELADY_LENGTH, BELADY_PAGES) for _ in range(BELADY_STRINGS)]  # the short strings
    for name, policy in (("FIFO", fifo), ("OPT", opt), ("LRU", lru), ("CLOCK", clock)):  # each policy in turn
        found = []  # the strings on which this policy shows the anomaly
        for refs in tests:  # every string
            counts = [policy(refs, n) for n in range(1, BELADY_PAGES + 1)]  # faults with 1 to 6 frames
            if anomaly(counts):  # one more frame gave MORE faults somewhere
                found.append((refs, counts))  # remember the string and its counts
        print(f"  {name:<6} more faults with more frames in {len(found):>3} of {len(tests):,} strings")  # the tally
        if found and name == "FIFO":  # show the first FIFO example in full
            refs, counts = found[0]  # the first one found
            print(f"         first example: {' '.join(map(str, refs))}")  # the string itself
            print(f"         faults with 1-{BELADY_PAGES} frames: {counts}")  # its fault counts


# ---------------------------------------------------------------------------
# Processor scheduling: each policy takes a list of (name, arrival, service) and returns {name: finish time}
# Time moves in whole units. A process that arrives at time t joins the ready queue before a process
# preempted at the same time t. Ties go to the process that arrived earlier.
# ---------------------------------------------------------------------------
def fcfs(procs):  # first come, first served: run each process to the end, in order of arrival
    finish = {}  # finish time of each process
    now = 0  # the simulated clock
    for name, arrival, service in sorted(procs, key=lambda p: p[1]):  # in arrival order (sorting keeps the listed order on ties)
        now = max(now, arrival)  # if the processor is idle, wait for this process to arrive
        now += service  # it runs to the end without interruption
        finish[name] = now  # and finishes here
    return finish  # every finish time


def spn(procs):  # shortest process next: when the processor is free, run the waiting process with the smallest service time
    waiting = sorted(procs, key=lambda p: p[1])  # processes that have not started yet, in arrival order
    finish = {}  # finish time of each process
    now = 0  # the simulated clock
    while waiting:  # until every process has run
        ready = [p for p in waiting if p[1] <= now]  # the ones that have already arrived
        if not ready:  # nobody has arrived yet...
            now = waiting[0][1]  # ...so the processor idles until the next arrival
            continue  # and decides again
        chosen = min(ready, key=lambda p: (p[2], p[1]))  # the smallest service time; ties go to the earlier arrival
        waiting.remove(chosen)  # it starts now...
        now += chosen[2]  # ...and runs to the end (no preemption)
        finish[chosen[0]] = now  # its finish time
    return finish  # every finish time


def round_robin(procs, quantum):  # round robin: each process runs at most `quantum` units, then goes to the back of the queue
    pending = deque(sorted(procs, key=lambda p: p[1]))
    left = {name: service for name, arrival, service in procs}
    ready = deque()
    finish = {}
    now = 0
    while pending or ready:
        while pending and pending[0][1] <= now:
            ready.append(pending.popleft()[0])
        if not ready:
            now = pending[0][1]
            continue
        name = ready.popleft()
        run = min(quantum, left[name])
        now += run
        left[name] -= run
        while pending and pending[0][1] <= now:
            ready.append(pending.popleft()[0])
        if left[name] == 0:
            finish[name] = now
        else:
            ready.append(name)
    return finish


def hrrn(procs):  # highest response ratio next: like SPN, but choose the largest R = (waiting time + service) / service
    waiting = sorted(procs, key=lambda p: p[1])
    finish = {}
    now = 0
    while waiting:
        ready = [p for p in waiting if p[1] <= now]
        if not ready:
            now = waiting[0][1]
            continue
        chosen = max(ready, key=lambda p: ((now - p[1] + p[2]) / p[2], -p[1]))
        waiting.remove(chosen)
        now += chosen[2]
        finish[chosen[0]] = now
    return finish


def scheduling_results(procs, finish):  # turnaround and normalized turnaround for every process
    rows = []  # one (name, arrival, service, finish, Tr, Tr/Ts) tuple per process
    for name, arrival, service in procs:  # in the listed order
        tr = finish[name] - arrival  # turnaround time: from arrival to finish
        rows.append((name, arrival, service, finish[name], tr, tr / service))  # normalized turnaround: Tr divided by the service time Ts
    return rows  # the table


SCHEDULERS = (("RR q=20", lambda p: round_robin(p, 20)), ("FCFS", fcfs), ("SPN", spn), ("RR q=1", lambda p: round_robin(p, 1)), ("RR q=4", lambda p: round_robin(p, 4)), ("HRRN", hrrn))  # B-g: compare a large quantum of 20 with the original schedulers


FIVE = [("A", 0, 5), ("B", 1, 7), ("C", 3, 2), ("D", 4, 4), ("E", 6, 1)]  # Experiment 3's workload: (name, arrival time, service time)


def experiment_five():  # every policy on a small workload you can check by hand
    print("\nExperiment 3: five processes (name arrival service): " + "  ".join(f"{n} {a} {s}" for n, a, s in FIVE))  # a title with the workload
    for label, policy in SCHEDULERS:  # one block per policy
        rows = scheduling_results(FIVE, policy(FIVE))  # run it and measure (an unwritten TODO stops here)
        cells = "  ".join(f"{name}:{fin:>3}" for name, _, _, fin, _, _ in rows)  # the finish times
        mean_tr = sum(r[4] for r in rows) / len(rows)  # mean turnaround
        mean_norm = sum(r[5] for r in rows) / len(rows)  # mean normalized turnaround
        print(f"  {label:<7} finish  {cells}   mean Tr {mean_tr:5.2f}   mean Tr/Ts {mean_norm:4.2f}")  # one line per policy


def random_workload(rng, count):  # `count` processes with random arrival gaps and random service times
    procs = []  # the workload being built
    now = 0  # arrival time of the next process
    for i in range(1, count + 1):  # P1, P2, ...
        now += round(rng.expovariate(1 / MEAN_GAP))  # the gap to this arrival: exponentially distributed, rounded to whole units (0 allowed)
        service = max(1, round(rng.expovariate(1 / MEAN_SERVICE)))  # its service time: exponential too, rounded, at least 1
        procs.append((f"P{i}", now, service))  # one process
    return procs  # the whole workload


def experiment_random():  # every policy on a large random workload, split by job length
    rng = random.Random(SEED + 2)  # a separate generator (seed 2028) for this experiment
    procs = random_workload(rng, NUM_PROCS)  # the workload
    total = sum(p[2] for p in procs)  # all the processor work there is
    print(f"\nExperiment 4: {NUM_PROCS} random processes (mean service {total / NUM_PROCS:.2f}, processor busy about {100 * total / fcfs(procs)[procs[-1][0]]:.0f}% of the time)")  # a title; FCFS never idles while work waits, so its last finish is the makespan
    by_length = sorted(range(NUM_PROCS), key=lambda i: (procs[i][2], i))  # process positions from shortest to longest service time
    third = NUM_PROCS // 3  # how many processes form a third
    short, long_ = set(by_length[:third]), set(by_length[-third:])  # the shortest third and the longest third
    print("  policy    mean Tr/Ts   shortest third   longest third   worst Tr/Ts   longest wait")  # the header
    for label, policy in SCHEDULERS:  # one row per policy
        rows = scheduling_results(procs, policy(procs))  # run and measure (an unwritten TODO stops here)
        norm = [r[5] for r in rows]  # every normalized turnaround
        mean = lambda idx: sum(norm[i] for i in idx) / len(idx)  # the mean over a set of positions
        wait = max(r[4] - r[2] for r in rows)  # the longest time any process spent NOT running: Tr minus its service time
        print(f"  {label:<8} {mean(range(NUM_PROCS)):>10.2f} {mean(short):>16.2f} {mean(long_):>15.2f} {max(norm):>13.2f} {wait:>14}")  # the row


def main():  # runs the experiments in order
    for experiment in (experiment_faults, experiment_belady, experiment_five, experiment_random):  # 1, 2, 3, 4
        try:  # run one experiment
            experiment()  # if it reaches an unwritten TODO, NotWrittenYet jumps to the except below
        except NotWrittenYet as missing:  # a TODO was reached
            print(f"  -> stopped here: {missing}")  # say which one, then carry on with the next experiment


if __name__ == "__main__":  # true when the file is run directly (not imported)
    main()  # start the program