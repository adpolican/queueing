from dataclasses import dataclass
from collections import defaultdict
from typing import List, Dict

import matplotlib.pyplot as plt
import numpy as np


class Job:
    def __init__(self, length: int):
        self.length = length
        self.waitTime: int = 0

    def __eq__(self, other):
        return (self is other)


@dataclass
class Server:
    name: str
    busy: bool = False

    def assign(self, job: Job):
        self.job = job
        self.busy = True
        return job

    def step(self):
        if self.busy:
            self.job.length -= 1
        if self.busy and self.job.length == 0:
            self.busy = False
            finishedJobs.append(self.job)
        return

    def __eq__(self, other):
        return (self is other)


NAMES = 'a b c d e'.split()
ARRIVAL_RATES = dict(zip(NAMES, [10, 20, 7, 30, 3]))
SERVICE_TIMES = dict(zip(NAMES, [1, 1, 2, 1, 10]))

TOTAL_SERVERS = 100
TIME_STEPS = 500

DECREASE_COEF = 0.5
INCREASE_CONST = 1

STARTING_SHARES = 1

jobData = []
shareData = []
serverData = []
waitingData = []
finishedJobs: List[Job] = []

jobs: Dict[str, List[Job]] = defaultdict(list)
servers: Dict[str, List[Server]] = defaultdict(list)
starving = {name: True for name in NAMES}
shares = {name: STARTING_SHARES for name in NAMES}


def adjustShares(shares, starving):
    redist = any([name for name, comp in starving.items() if not comp])
    for name in NAMES:
        if redist and not starving[name]:
            shares[name] = int(DECREASE_COEF*shares[name])
        if redist and starving[name]:
            shares[name] += INCREASE_CONST
        shares[name] = max(1, shares[name])
    return shares


def adjustServers(servers, shares):
    totalShares = sum(shares.values())
    proposedServerCounts = {}
    killable = {name: len([s for s in servers[name] if not s.busy])
                for name in NAMES}
    for name, share in shares.items():
        targetServerCount = int((share/totalShares) * (TOTAL_SERVERS))
        targetServerCount = max(targetServerCount, 1)  # Always keep 1
        serverDelta = targetServerCount - len(servers[name])

        minimumPossible = len(servers[name]) - killable[name]
        proposal = len(servers[name]) + serverDelta
        proposedServerCounts[name] = max(proposal, minimumPossible)

    # Bound the total server count to TOTAL_SERVERS
    attempt = 0
    while sum(proposedServerCounts.values()) > TOTAL_SERVERS:
        name = NAMES[attempt % len(NAMES)]
        serverDelta = proposedServerCounts[name] - len(servers[name])
        minimumPossible = len(servers[name]) - killable[name]
        if proposedServerCounts[name] - minimumPossible > 0:
            proposedServerCounts[name] -= 1

    # Adjust the actual server counts
    for name, propCount in proposedServerCounts.items():
        killable = [server for server in servers[name] if not server.busy]
        serverDelta = propCount - len(servers[name])
        if serverDelta > 0:
            servers[name] += [Server(name) for _ in range(serverDelta)]
        if serverDelta < 0:
            toKill = killable[:abs(serverDelta)]
            servers[name] = [w for w in servers[name] if w not in toKill]
    return servers


def trackWaiting(jobList):
    totalWaiting = 0
    totalQueueing = 0.01
    maxWaiting = 0
    for job in jobList:
        totalWaiting += job.waitTime
        maxWaiting = max(job.waitTime, maxWaiting)
        totalQueueing += 1
    return [maxWaiting, totalWaiting/totalQueueing]


def asPartsOfWhole(arr):
    wholes = np.sum(arr, axis=0)
    percents = arr / wholes
    return percents


def createJobs(jobs):
    for name, jobsToMake in ARRIVAL_RATES.items():
        jobs[name] += [Job(SERVICE_TIMES[name]) for _ in range(jobsToMake)]
    return jobs


def assignServers(servers, jobs):
    starving = {}
    for name in NAMES:
        availableServers = [w for w in servers[name] if not w.busy]
        assignedJobs = []
        for job, server in zip(jobs[name], availableServers):
            assignedJobs.append(server.assign(job))

        jobs[name] = [j for j in jobs[name] if j not in assignedJobs]
        newJobCount = len(jobs[name])
        starving[name] = (newJobCount > 0)
    return starving


def addWaitTime(jobs):
    for name, waitingJobs in jobs.items():
        for job in waitingJobs:
            job.waitTime += 1
    return jobs


def executeJobs(servers):
    for serverList in servers.values():
        for server in serverList:
            server.step()
    return servers


def makeStatusStr(names):
    msgs = [f'{name}: {len(jobs[name])}j-{shares[name]}s-{len(servers[name])}w'
            for name in names]
    return ' '.join(msgs)


if __name__ == '__main__':
    for step in range(TIME_STEPS):
        shares = adjustShares(shares, starving)
        servers = adjustServers(servers, shares)
        jobs = addWaitTime(jobs)

        waitingData.append(trackWaiting(finishedJobs))
        finishedJobs = []

        jobs = createJobs(jobs)
        starving = assignServers(servers, jobs)
        servers = executeJobs(servers)

        jobData.append([len(jobs[name]) for name in NAMES])
        shareData.append([shares[name] for name in NAMES])
        serverData.append([len(servers[name]) for name in NAMES])

        '''
        status = makeStatusStr(names)
        print(f"time:{step} {status}")
        '''

    X = np.arange(TIME_STEPS)
    spacing = 3*TIME_STEPS/100
    X_ticks = np.arange(0, TIME_STEPS, spacing)
    fig, axs = plt.subplots(3)

    waitArr = np.array(waitingData).T
    axs[0].set_title('Waiting Time', y=0.75)
    axs[0].plot(X, waitArr[0], label='max waiting')
    axs[0].plot(X, waitArr[1], label='mean waiting')
    axs[0].set_ylabel('time (s)')
    axs[0].legend(loc='upper right')

    jobArr = np.array(jobData).T
    axs[1].set_title('Jobs in Queue', y=0.75)
    axs[1].set_ylabel('Jobs')
    axs[1].stackplot(X, jobArr, labels=NAMES)
    axs[1].legend(loc='upper right')

    serverArr = np.array(serverData).T
    axs[2].set_title('Servers Per Job Type', y=0.75)
    axs[2].stackplot(X, serverArr, labels=NAMES)
    axs[2].set_ylabel('Server')
    axs[2].legend(loc='upper right')
    plt.setp(axs, xticks=X_ticks)

    plt.show()
