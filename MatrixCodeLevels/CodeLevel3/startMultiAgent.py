from multiprocessing import Process
from multi_agent_v7 import main_multi_agent

if __name__ == '__main__':
    starts = list(range(1, 2000, 1000))
    procs = []

    for start_index in starts:
        proc = Process(target=main_multi_agent,
                       args= ('127.0.0.1:8090', '/home/ronmintz/MatrixCodeLevels/CodeLevel2/GitHubStore/gh_store2017ESX/gh.sqlite', 'users2017', start_index, 1000, 65131614))
        procs.append(proc)
        proc.start()

    for proc in procs:
        proc.join()
        
