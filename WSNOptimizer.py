import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
from shapely.ops import unary_union
import pprint
from random import gauss, sample,choices,uniform
import win32com.client as wncl
import heapq
speaker = wncl.Dispatch("SAPI.SpVoice")
import pandas as pd
class WSNOptimizer():
    def __init__(self):
        self.coverage_weight,self.energy_weight=1,1
        """The constructor method initialises the necessary variables.
        params:
        1 num_sensors: integer value
        2 x_len :integer valued
        3 y_len:ineteger valued
        4 r_sense(radius) , rcom
        5 energy"""
        speaker.Speak("Enter the number of sensors to be deployed and the x and y lengths of the target region.")
        self.num_sensors,self.x_len,self.y_len=list(map(int,input("Enter the number of sensors to be deployed and the x and y lengths of the target region.").split(" ")))
        self.area=self.x_len*self.y_len
        speaker.Speak("Enter sensing radius and communication radius.")
        self.radius,self.rcom=list(map(float,input("enter sensing radius and communication radius.").split(" ")))
        speaker.Speak("Enter the energy for each sensor")
        self.energy=int(input("Enter the energy for each sensor"))
    def initialise_population(self):
        """This function is used to initialise population,depending upon number of sensors to be deployed.
        Population_size=2*num_sensors
        Use of real number encoding
        returns a 3-D list of floating point numbers."""
        population = []
        while len(population) != 2*self.num_sensors:
            member = []
            for j in range(self.num_sensors):
                val_1 = round(np.random.uniform(0, self.x_len), 3)
                val_2 = round(np.random.uniform(0, self.y_len), 3)
                member.append([val_1, val_2])
            population.append(member)
        return population
    def coverage_eval(self,generation,useless_nodes_bag):
        """returns the Coverage values for all the members of a population, Circles made by sensing radius and communication radius.
        params: generation"""
        Coverage = []
        Circle_Bag = []
        Communication_circle_bag=[]
        # Points = []
        for i in range(len(generation)):
            useless_nodes = useless_nodes_bag[i]
            gen = generation[i]
            circles = []
            comm_circles=[]
            # X = []
            # Y = []
            useless_circles=[]
            for j in range(len(gen)):
                x = gen[j][0]
                # X.append(x)
                y = gen[j][1]
                # Y.append(y)
                circle = Point((x,y)).buffer(self.radius)
                if j in useless_nodes:
                    useless_circles.append(circle)
                comm_circle=Point((x,y)).buffer(self.rcom)
                circles.append(circle)
                comm_circles.append(comm_circle)
            # Points.append([X, Y])
            union = unary_union(circles)
            useless_union = unary_union(useless_circles)
            coverage = (union.area - useless_union.area) / self.area
            Coverage.append(coverage)
            Circle_Bag.append(circles)
            Communication_circle_bag.append(comm_circles)
        return Coverage, Circle_Bag,Communication_circle_bag
    def dijkstra(self, graph, start, end):
        """returns The shortest path from start node to end node in the graph.
        params: graph ,start(starting node in graph) ,end(ending node i.e. HECN)"""
        # Initialize the min-heap
        min_heap = [(0, start)]  # (distance, node)
        distances = {node: float(1e9) for node in graph}
        distances[start] = 0
        previous_nodes = {node: None for node in graph}
        while min_heap:
            current_distance, current_node = heapq.heappop(min_heap)
            # Early exit if we reach the end node
            if current_node == end:
                break
            # Skip processing if the distance is not optimal
            if current_distance > distances[current_node]:
                continue
            # Check all neighbors of the current node
            for neighbor, weight in graph[current_node].items():
                distance = current_distance + weight
                # Only consider this path if it's better
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(min_heap, (distance, neighbor))
        # Reconstruct the shortest path
        path = []
        current_node = end
        while current_node is not None:
            path.append(current_node)
            current_node = previous_nodes[current_node]
        path = path[::-1]  # Reverse the path to go from start to end
        if distances[end] == float(1e9):
            return []
        else:
            return path
    def create_graph(self,l1):
        """returns the graph for a memeber of the population || type: dictionary of dictionary
        weight of graph is initialised to 1/energy
        2 nodes are connected only if distance between them is less than (2*rcom)"""
        def distance( pt1, pt2):
            return ((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2) ** 0.5
        energy = 1 / self.energy
        graph = {}
        for i in range(len(l1)):
            graph[i] = {}
            for j in range(len(l1)):
                if j == i:
                    continue
                elif i > j:
                    if i in graph[j].keys():
                        graph[i][j] = graph[j][i]
                    continue
                else:
                    currdist = distance(l1[i], l1[j])
                    if currdist < 2*self.rcom:
                        graph[i][j] = energy
        return graph
    def update_graph(self,st_path, Graph):
        """returns graph with updated weights after using dijkstra function
        params: 1) graph ,2) st_path: output of dijkstra function"""
        for i in range(len(st_path) - 1):
            node = st_path[i]
            weight_key = Graph[node].keys()
            for j in weight_key:
                weight = Graph[node][j]
                weight = round(1 / ((1 / weight) - 1), 3)
                if (weight < 0):
                    return {}
                Graph[node][j] = weight
        return Graph
    def energy_calc_for_phenotype(self,graph):
        """returns lifetime , energy consumed and record of points from each node to hecn(High Energy Communication Node.)
         params : graph"""
        previous_sense = []
        curr_sense = []
        hecn = len(graph) - 1
        count = 0
        flag = 0
        st_path_bag = []
        useless_nodes = []
        while True:
            for i in range(len(graph) - 1):
                if count==0:
                    st_path = self.dijkstra(graph, i, hecn)
                    st_path_bag.append(st_path)
                    if not st_path:
                        useless_nodes.append(i)
                    graph = self.update_graph(st_path, graph)
                else:
                    st_path=st_path_bag[i]
                    graph=self.update_graph(st_path,graph)
                curr_sense.append(st_path)
                if (len(graph) == 0):
                    if (i != hecn - 1):
                        flag = 1
                        break
                    else:
                        previous_sense = curr_sense.copy()
                        curr_sense = []
                        count += 1
                        flag = 1
                        break
            if (flag == 1):
                break
            previous_sense = curr_sense.copy()
            curr_sense = []
            count += 1
        count = count / (self.energy)  # count is working as lifetime from this line onwards
        consumed_energy = 0
        active = 0
        for i in range(len(previous_sense)):
            if len(previous_sense[i]) != 0:
                active += 1
                consumed_energy += len(previous_sense[i]) - 1
        active = active + 1 if active == 0 else active
        return count, (consumed_energy / active), previous_sense,useless_nodes

    def energy_eval(self,generation):
        """returns Energy and Lifetime for the whole generation"""
        Energy = []
        Life = []
        Path_Bag = []
        useless_nodes_bag=[]
        for i in range(len(generation)):
            paths_of_node = []
            graph = self.create_graph(generation[i] + [[self.x_len / 2, self.y_len / 2]])
            lifetime, e_consume, paths,useless_nodes = self.energy_calc_for_phenotype(graph)
            Energy.append(e_consume)
            useless_nodes_bag.append(useless_nodes)
            Life.append(lifetime)
            for j in range(len(paths)):
                X, Y = [], []
                if (paths[j] == {}):
                    X.append([generation[i][j][0]])
                    Y.append([generation[i][j][1]])
                    paths_of_node.append([X, Y])
                    continue
                else:
                    X.extend([generation[i][paths[j][k]][0] for k in range(len(paths[j]) - 1)])
                    X.append(self.x_len / 2)
                    Y.extend([generation[i][paths[j][k]][1] for k in range(len(paths[j]) - 1)])
                    Y.append(self.y_len / 2)
                paths_of_node.append([X, Y])
            #         print(len(paths_of_node))
            Path_Bag.append(paths_of_node)
        return Energy, Life, Path_Bag,useless_nodes_bag
    def fitness_sharing(self,population, fitnesses, niche_radius=1.0):
        """returns fitness values by modifying fitnesss for those occuring very frequently in generation."""
        shared_fitnesses = []
        for i, individual in enumerate(population):
            sharing_sum = 0
            for j, other in enumerate(population):
                if i != j:
                    distance = np.linalg.norm(np.array(individual) - np.array(other))
                    if distance < niche_radius:
                        sharing_sum += 1 - (distance / niche_radius)
            shared_fitnesses.append(fitnesses[i] / (1 + sharing_sum))
        return shared_fitnesses
    def fit_eval(self,generation,epoch,sharing=True,plot=True):
        Energy,Life,Path_bag,useless_nodes_bag=self.energy_eval(generation)
        Coverage, Circle_Bag,Communication_circle_bag = self.coverage_eval(generation,useless_nodes_bag)
        fitness = [((self.coverage_weight*i)+(self.energy_weight*j))  for i,j in zip(Coverage,Life)]
        if (plot == True):
            ind = fitness.index(max(fitness))
            paths=Path_bag[ind]
            circles = Circle_Bag[ind]
            comm_circles=Communication_circle_bag[ind]
            plt.xlim([0, self.x_len])
            plt.ylim([0, self.y_len])
            for circle,comm_circle,i in zip(circles,comm_circles,range(len(paths))):
                x, y = circle.exterior.xy
                xcom,ycom=comm_circle.exterior.xy
                plt.plot(xcom,ycom,'m',linestyle="dashdot")
                plt.plot(x, y, 'g')
                plt.plot(paths[i][0], paths[i][1], "b", marker="o", mfc="r",mec="r")
            plt.title(f"Generation:{epoch} Coverage:{Coverage[ind]:.5f} Lifetime:{Life[ind]:.5f} EnergyConsumption:{Energy[ind]:.5f}")
            plt.plot([self.x_len/2], [self.y_len/2], marker="*", markersize=30)
            print(f"Generation:{epoch} Coverage:{Coverage[ind]:.5f} Lifetime:{Life[ind]:.5f} EnergyConsumption:{Energy[ind]:.5f}")
        if(sharing==True and epoch<=2):
            fitness=self.fitness_sharing(generation,Coverage)
        return fitness, Coverage,Life,Energy
    def selection(self,generation, fitness):
        return choices(generation, weights=fitness, k=len(generation))
    def crossover(self,parents, alpha=0.2):
        size = len(parents)
        child = []
        while len(child) != size:
            for i in range(size - 1):
                parent_1, parent_2 = parents[i], parents[i + 1]
                if (parent_1 != parent_2):
                    child_1, child_2 = [], []
                    for j in range(len(parent_1)):
                        p_1, p_2 = parent_1[j], parent_2[j]
                        r = uniform(-alpha, (1 + alpha))
                        child_1.append([round(np.clip((p_1[0] + (r * (p_2[0] - p_1[0]))), 0, self.x_len), 3),
                                        round(np.clip((p_1[1] + (r * (p_2[1] - p_1[1]))), 0, self.y_len), 3)])
                        child_2.append([round(np.clip((p_2[0] + (r * (p_1[0] - p_2[0]))), 0, self.x_len), 3),
                                        round(np.clip((p_2[1] + (r * (p_1[1] - p_2[1]))), 0, self.y_len), 3)])
                    if (child_1 not in child):
                        child.append(child_1)
                    if (child_2 not in child):
                        child.append(child_2)
                    if (len(child) == size):
                        break
                else:
                    continue
        return child
    def mutation(self,gen, epoch, max_epochs=1000):
        new_gen = gen.copy()
        # Determine how many sensors to mutate based on how far along we are in generations
        sigma = 1.0 * (1 - (epoch / (max_epochs * (self.x_len*self.y_len))))
        fraction_to_mutate = max(0.1, (1 - epoch / max_epochs))  # Decrease mutation over time
        num_sensors_to_mutate = int(fraction_to_mutate * len(gen[0]))
        num_mutate = int(fraction_to_mutate * len(gen))
        for i in sample(range(len(gen)),num_mutate):
            individual = gen[i].copy()
            indices_to_mutate = sample(range(len(individual)), num_sensors_to_mutate)
            for index in indices_to_mutate:
                x, y = individual[index]
                new_x = round(np.clip(x + gauss(0, sigma), 0, self.x_len), 3)
                new_y = round(np.clip(y + gauss(0, sigma), 0, self.y_len), 3)
                individual[index] = [new_x, new_y]
            new_gen[i] = individual
        return new_gen
    def optimise(self):
        self.dic={"GenerationNumber":[],"Coverage":[],"LifeTime":[],"EnergyConsumption":[]}
        speaker.Speak("Enter the maximum number of iterations.")
        max_epoch=int(input("Enter the maximum number of iterations."))
        speaker.Speak("Would you like to perform fitness sharing.")
        share=bool(input("Would you like to perform fitness sharing."))
        speaker.Speak("Enter weights for Coverage and Energy Consumption respectively.")
        self.coverage_weight,self.energy_weight=list(map(float,input("Enter weights for Coverage and Energy respectively.").split(" ")))
        generation=self.initialise_population()
        epoch=0
        flag=0
        self.nodes={"X":[],"Y":[]}
        while (epoch!=max_epoch):
            plt.clf()
            fit1,cov1,life1,energy1=self.fit_eval(generation,epoch,share)
            plt.pause(1)
            ind=fit1.index(max(fit1))
            self.dic["GenerationNumber"].append(epoch)
            self.dic["Coverage"].append(cov1[ind])
            self.dic["LifeTime"].append(life1[ind])
            self.dic["EnergyConsumption"].append(energy1[ind])
            if(max(cov1)>=(0.50) and max(life1)>=0.50):
                gen=np.array(generation[ind])
                self.nodes["X"]=gen[:,0]
                self.nodes["Y"]=gen[:,1]
                flag=1
                speaker.Speak("We have reached to satisfactory results and therefore algorithm terminates here.")
                plt.show()
                plt.plot(cov1,life1,"m", marker="o", mfc="r",mec="m")
                plt.xlabel("Coverage")
                plt.ylabel("LifeTime")
                plt.title("Graph b/w coverage & lifetime representing pareto optimal solutions")
                plt.grid(True)
                plt.show()
                break
            newgen=self.mutation(self.crossover(self.selection(generation,fit1)),epoch,max_epoch)
            fit2,cov2,life2,energy2=self.fit_eval(newgen,epoch,sharing=False,plot=False)
            def compare1(val):
                return fit1[generation.index(val)]
            def compare2(val):
                return fit2[newgen.index(val)]
            list1=sorted(generation,key=compare1,reverse=True)[:(len(generation)//2)]
            list2=sorted(newgen,key=compare2,reverse=True)[:(len(generation)//2)]
            generation=list1+list2
            epoch+=1
        if(flag==0):
            fit1,cov1,life1,energy1=self.fit_eval(generation,epoch,sharing=False)
            ind=fit1.index(max(fit1))
            gen=np.array(generation[ind])
            self.dic["GenerationNumber"].append(epoch)
            self.dic["Coverage"].append(cov1[ind])
            self.dic["LifeTime"].append(life1[ind])
            self.dic["EnergyConsumption"].append(energy1[ind])
            self.nodes["X"]=gen[:,0]
            self.nodes["Y"]=gen[:,1]
            plt.show()
            plt.plot(cov1, life1, "m", marker="o", mfc="r", mec="m")
            plt.xlabel("Coverage")
            plt.ylabel("LifeTime")
            plt.title("Graph b/w coverage & lifetime representing pareto optimal solutions")
            plt.grid(True)
            plt.show()
        self.df=pd.DataFrame(self.dic)
        self.df2=pd.DataFrame(self.nodes)
        plt.plot(self.df['Coverage'],self.df['LifeTime'], "m", marker="o", mfc="r", mec="m")
        plt.xlabel("Coverage")
        plt.ylabel("LifeTime")
        plt.title("Graph b/w coverage & lifetime (across generations) representing pareto optimal solutions")
        plt.grid(True)
        plt.show()
        if flag==0:
            speaker.Speak("Final results are listed below.")
        print("The Coverage, LifeTime, EnergyConsumption history across generations is given below.\n")
        print(self.df)
        print("Sensor Placement Points listed below.\n")
        print(self.df2)
if __name__=="__main__":
    wsn1=WSNOptimizer()
    wsn1.optimise()


















