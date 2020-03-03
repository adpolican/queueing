from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Job:
    length: int


@dataclass
class Worker:
    name: str
    busy: bool = False

    def assign(self, job: Job):
        self.busy = True

    def step(self):
        try:
            self.job.length -= 1
            self.busy = (self.job.length == 0)
        except AttributeError:
            pass
        return


names = 'a b c d'.split()
jobArrivals = [1, 5, 10, 15]

totalWorkers = 50
timeSteps = 100


decrease = 0.8
increase = 1

if __name__ == '__main__':
    queue = defaultdict(list)
    workers = defaultdict(int)
    jobs = defaultdict(int)
    starving = {name: True for name in names}
    shares = {name: 10 for name in names}

    for step in range(timeSteps):
        # Readjust the shares that workers get
        redist = any([name for name, comp in starving.items() if not comp])
        for name in names:
            if redist and not starving[name]:
                shares[name] = int(decrease*shares[name])
            if redist and starving[name]:
                shares[name] += increase
            shares[name] = max(1, shares[name])
         
        # Create more workers according to shares
        totalShares = sum(shares.values())
        for name, share in shares.items():
            workerCount = int((share/totalShares) * (totalWorkers-len(names)))
            workers[name] = max(1, workerCount)

        # Consume jobs
        starving = {}
        for name, newJobs in zip(names, jobArrivals):
            oldJobCount = jobs[name]
            jobs[name] += newJobs
            jobs[name] = max(jobs[name] - workers[name], 0)
            newJobCount = jobs[name]
            starving[name] = (newJobCount > 0)

        msg = ' '.join([f'{name}: {shares[name]}s-{workers[name]}w-{jobs[name]}j' for name in names])
        print(f'time:{step} {msg}')
            

            
