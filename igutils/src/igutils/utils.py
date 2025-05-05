def check_consistency(grid):
	"""
	If this function fails, then it means that some in umbering is not right in the file.
	"""
	
	for i in grid.vertex.values:
		for e in grid.edges_of_vertex.values.T[i]:
			if e > 0:
				for c in grid.adjacent_cell_of_edge.values.T[e-1]:
					for v in grid.vertex_of_cell.values.T[c-1]:
						if v-1!=i and not v in grid.vertices_of_vertex.values.T[i,:]:
							print(f"Error for vertex i={i}, with edge e={e}, with cell c={c} and vertex v={v} is not in {grid.vertices_of_vertex.values.T[i,:]}")
							assert False

def find_pentagons_vertices(grid):
	return [i for x, i in zip(grid.vertices_of_vertex.values[5,:], range(len(grid.vertices_of_vertex.values[5,:]))) if int(x) <= 0]

def short_path_vertices(v1, v2s, grid):
    print(f"computing {v1} -> {v2s}")
    queue = [v1]
    mark = {v1: 0}
    #i = 0
    while queue:
        u = queue.pop(0)
        #i = i+1
        if u in v2s:
            print(f"{v1} to {u} path is {mark[u]} long")
        for v in grid.vertices_of_vertex.values[:,u-1]:
            if v > 0 and not v in mark:
                mark[v] = mark[u] + 1
                #print(f"{i} -> {u} -> {v} (mark = {mark[u]})         ", end='\r')
                queue.append(v)
    return mark

def backtrack_vertices(src, dst, mark, grid):
	path1 = [dst+1]
	u = dst+1
	#distance = mark[dst]
	while u != src+1:
		vs = grid.vertices_of_vertex.values[:, u-1]
		#print(f"u = {u}")
		ok = False
		for v in vs:
			if v > 0:
				#print(f"    src = {src}, u = {u}, mark[u] = {mark[int(u)]}, v = {v}, mark[v] = {mark[int(v)]}")
				if mark[v] == mark[u]-1:
					#distance = mark[v]
					ok = True
					path1.insert(0, int(v))
					u = v
					break
		if not ok:
			raise Exception("WHATTT!?!?")
		#print(path1)
	return path1

def pentagons_paths_vertices(grid):
	import gc

	eov = find_pentagons_vertices(grid)
	#short_path(f['edge_vertices'][0,eov[0]-1], f['vertices_of_vertex'][0,f['edge_vertices'][1,eov[0]-1]])
	paths = []
	for i in range(0, len(eov)):
		mark = short_path_vertices(eov[i]+1, [x+1 for x in eov], grid)
		paths.append([])
		for n in range(1, len(eov)):
			paths[-1].append(backtrack_vertices(eov[i], eov[n], mark, grid))
		del(mark)
		gc.collect()
	return paths

def mark_rhomboid(closed_path, inner_vertex, grid):
	None