from multiprocessing import Process
from multi_agent_v4A import main_multi_agent

if __name__ == '__main__':
    starts = [1]
    procs = []

    for start_index in starts:
        proc = Process(target=main_multi_agent,
                       args= ('127.0.0.1:8091', '/scratch/ron/JulyChallenge/GitHubStore/ghstore_2017/gh.sqlite', 'users2017', start_index, 1000, 1000))
        procs.append(proc)
        proc.start()

    for proc in procs:
        proc.join()
        
