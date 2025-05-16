from typing import Any, Union, List, Tuple
import numpy as np
import xarray as xr
import matplotlib.pylab as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class Rhomboid:
	def __init__(self, a: int,b: int, c: int, d: int):
		r'''
		        A
	    	    /\ 
		       /  \ 
		     B \  / C
        	    \/
		       D
    	'''
		self.t = (a, b, c, d)

	@property
	def upsidedown(self):
		return Rhomboid(self.t[3], self.t[1], self.t[2], self.t[0])	
	
	@property
	def mirrored(self):
		return Rhomboid(self.t[0], self.t[2], self.t[1], self.t[3])	

	def __getitem__(self, i):
		return self.t[i]

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
    #print(f"computing {v1} -> {v2s}")
    queue = [v1]
    mark = {v1: 0}
    #i = 0
    while queue:
        u = queue.pop(0)
        #i = i+1
        # if u in v2s:
        #     print(f"{v1} to {u} path is {mark[u]} long")
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
	paths = {}
	for i in range(0, len(eov)):
		mark = short_path_vertices(eov[i]+1, [x+1 for x in eov], grid)
		for n in range(0, len(eov)):
			paths[(eov[i]+1,eov[n]+1)] = backtrack_vertices(eov[i], eov[n], mark, grid)
		del(mark)
		gc.collect()
	return paths

def find_rhomboids(eov, grid, paths, path_length):
	# Idetifying rhomboids
	# Find the "ring" on the poles and in the northern and south emisphere
	north_emi = []
	south_emi = []
	north_pole = None
	south_pole = None
	for u in eov:
		if grid.latitude_vertices.values[u] > 0 and grid.latitude_vertices.values[u] < 1.5:
			north_emi.append(u+1)
		if grid.latitude_vertices.values[u] < 0 and grid.latitude_vertices.values[u] > -1.5:
			south_emi.append(u+1)
		if grid.latitude_vertices.values[u] > 1.5:
			north_pole = u+1
		if grid.latitude_vertices.values[u] < -1.5:
			south_pole = u+1
	#print(north_emi, south_emi, north_pole, south_pole)

	# find the 5 rhomboids in the north emiosphere
	#        A
	#       /\
	#      /  \
	#    B \  / C
    #       \/
	#       D
	north_rhomboids = []
	A = north_pole
	for ui in range(5):
		for vi in range(ui+1,5):
			if len(paths[(north_emi[ui], north_emi[vi])]) == path_length:
				# TODO: need to check orientation of the paths...
				B = north_emi[ui]
				C = north_emi[vi]
				# finding D
				for i in range(5):
					if len(paths[B, south_emi[i]]) == path_length and len(paths[C, south_emi[i]]) == path_length:
						D = south_emi[i]
						north_rhomboids.append(Rhomboid(A, B, C, D))
	south_rhomboids = []
	A = south_pole
	for ui in range(5):
		for vi in range(ui+1,5):
			if len(paths[(south_emi[ui], south_emi[vi])]) == path_length:
				# TODO: need to check orientation of the paths...
				B = south_emi[ui]
				C = south_emi[vi]
				# finding D
				for i in range(5):
					if len(paths[B, north_emi[i]]) == path_length and len(paths[C, north_emi[i]]) == path_length:
						D = north_emi[i]
						south_rhomboids.append(Rhomboid(A, B, C, D))

	return north_rhomboids, south_rhomboids

# Marking the vertices inside in the interesting region
def mark_rhomboid(rhomboid, paths, grid): # rhomboid = (A, B, C, D)
	#print(paths.keys())
	A = rhomboid[0]
	B = rhomboid[1]
	C = rhomboid[2]
	D = rhomboid[3]
	
	mark = {}
	for u in paths[(A,B)]:
		mark[u] = True
	for u in paths[(A,C)]:
		mark[u] = True
	for u in paths[(B,D)]:
		mark[u] = True
	for u in paths[(C,D)]:
		mark[u] = True

	# Find a vertex inside the rhomboid: the second vertex of the path from the two middle points
	u = paths[(B, C)][1]

	mark[u] = True
	queue = [u]
	while queue:
		u = queue.pop()
		for v in grid.vertices_of_vertex.values[:,u-1]:
			if v > 0 and not v in mark:
				mark[v] = True
				queue.append(v)

	# Finding rows and columns for the strided order
	vertex_sequence = []
	ll = 0
	columns = paths[(A,B)]
	# Initialize the first row indices
	for u in columns:
		#print(u, end=" ")
		mark[u] = ll
		ll += 1
		vertex_sequence.append(u)
	rows = paths[(A,C)]
	#print()

	current_list = columns
	for i in rows[1:-1]: # first row already done
		mark[i] = ll 
		vertex_sequence.append(i)
		ll += 1
		next_list = [current_list[0]]
		v = i
		for u in current_list[1:]:
			set1 = [int(x) for x in grid.vertices_of_vertex.values.T[v-1] if int(x) in mark and type(mark[x]) == type(True)]
			set2 = [int(x) for x in grid.vertices_of_vertex.values.T[u-1] if int(x) in mark and type(mark[x]) == type(True)]
			intersect = [x for x in set1 if x in set2]
			#print(f'{ll=} {v=} {u=} {set1=} {set2=} {intersect=}')
			assert(len(intersect) == 1)
			mark[intersect[0]] = ll
			vertex_sequence.append(intersect[0])
			ll += 1
			v = intersect[0]
			next_list.append(v)
		current_list = next_list

	for u in paths[(C,D)]:
		#print(u, end=" ")
		mark[u] = ll
		vertex_sequence.append(u)
		ll += 1

	return vertex_sequence

class RenumberedGridVertices:
	def __init__(self, grid_file: str, **kwargs):
		verbose = False
		skip_check = False

		if 'verbose' in kwargs.keys():
			verbose = kwargs['verbose']

		if 'skip_check' in kwargs.keys():
			skip_check = kwargs['skip_check']

		verbose and print("Opening file")
		self._grid = xr.open_dataset(grid_file)

		try:
			print(self._grid.symmetry)
			is_icosahedron = False
		except:
			is_icosahedron = True

		if not is_icosahedron:
			raise Exception("The grid file contains a grid which is not an icosahedron")
		
		if not skip_check:
			verbose and print("Check consistency")
			check_consistency(self._grid)
		else:
			verbose and print("[SKIPPED] Check consistency")

		verbose and print("Find pentagons")
		self.eov = find_pentagons_vertices(self._grid)

		verbose and print("Find paths between pentagons")
		self._paths = pentagons_paths_vertices(self._grid)

		self.interesting_path_length = min([ len(x) for x in self.paths.values() if len(x)>1])

		verbose and print("Finding rhomboids")
		self.rhomboids_north, self.rhomboids_south = find_rhomboids(self.eov, self._grid, self._paths, self.interesting_path_length)

	def get_rhomboid_north(self, i: int):
		return self.rhomboids_north[i]

	def get_rhomboid_south(self, i: int):
		return self.rhomboids_south[i]

	def get_rhomboids_vsequence(self, rhomboid: Rhomboid):
		return mark_rhomboid(rhomboid, self._paths, self._grid)
	
	def get_cells(self, rhomboid: Rhomboid, **kwargs):
		with_color = False
		if 'with_color' in kwargs.keys():
			with_color = kwargs['with_color']

		rhomboid_seq = self.get_rhomboids_vsequence(rhomboid)
		out = []
		if with_color:
			for i in range(self.interesting_path_length-1):
				for j in range(self.interesting_path_length-1):
					v1 = rhomboid_seq[i*self.interesting_path_length+j]
					v2 = rhomboid_seq[(i+1)*self.interesting_path_length+j]
					v3 = rhomboid_seq[i*self.interesting_path_length+j+1]
					c1 = self.grid.cells_of_vertex.values[:,v1-1]
					c2 = self.grid.cells_of_vertex.values[:,v2-1]
					c3 = self.grid.cells_of_vertex.values[:,v3-1]
					intersect = [c for c in c1 if c in c2 and c in c3]
					assert(len(intersect) == 1)
					assert(intersect[0] != -1)
					out.append(int(intersect[0]-1))

			for i in range(self.interesting_path_length-1):
				for j in range(self.interesting_path_length-1):
					v1 = rhomboid_seq[(i+1)*self.interesting_path_length+j]
					v2 = rhomboid_seq[i*self.interesting_path_length+j+1]
					v3 = rhomboid_seq[(i+1)*self.interesting_path_length+j+1]
					c1 = self.grid.cells_of_vertex.values[:,v1-1]
					c2 = self.grid.cells_of_vertex.values[:,v2-1]
					c3 = self.grid.cells_of_vertex.values[:,v3-1]
					intersect = [c for c in c1 if c in c2 and c in c3]
					assert(len(intersect) == 1)
					assert(intersect[0] != -1)
					out.append(int(intersect[0]-1))
		else:
			for i in range(self.interesting_path_length-1):
				for j in range(self.interesting_path_length-1):
					v1 = rhomboid_seq[i*self.interesting_path_length+j]
					v2 = rhomboid_seq[(i+1)*self.interesting_path_length+j]
					v3 = rhomboid_seq[i*self.interesting_path_length+j+1]
					c1 = self.grid.cells_of_vertex.values[:,v1-1]
					c2 = self.grid.cells_of_vertex.values[:,v2-1]
					c3 = self.grid.cells_of_vertex.values[:,v3-1]
					intersect = [c for c in c1 if c in c2 and c in c3]
					assert(len(intersect) == 1)
					assert(intersect[0] != -1)
					out.append(int(intersect[0]-1))

					v1 = rhomboid_seq[(i+1)*self.interesting_path_length+j]
					v2 = rhomboid_seq[i*self.interesting_path_length+j+1]
					v3 = rhomboid_seq[(i+1)*self.interesting_path_length+j+1]
					c1 = self.grid.cells_of_vertex.values[:,v1-1]
					c2 = self.grid.cells_of_vertex.values[:,v2-1]
					c3 = self.grid.cells_of_vertex.values[:,v3-1]
					intersect = [c for c in c1 if c in c2 and c in c3]
					assert(len(intersect) == 1)
					assert(intersect[0] != -1)
					out.append(int(intersect[0]-1))
		return out

	def plot_rhomboid(self, rhomboid: Rhomboid, **kwargs):
		pltsize = (100, 80)
		if 'size' in kwargs.keys():
			assert(type(kwargs['size'] == Tuple[int, int]))
			pltsize = kwargs['size']

		vsequence = self.get_rhomboids_vsequence(rhomboid)
		fig = plt.figure(figsize=pltsize) # Need to find a way of setting the size right...
		ax = fig.add_subplot(1, 1, 1, projection=ccrs.Mollweide())
		ax.set_global()
		ax.add_feature(cfeature.LAND, zorder=0, edgecolor="black")
		pad = ''
		v = 0
		transformatio = ccrs.Geodetic()
		for v1, v2, v3, v4, v5, v6 in self._grid.vertices_of_vertex.values.T - 1:
			i = np.array([v, v1])
			for vi in [v1, v2, v3, v4, v5]:
				i = np.array([v, vi])
				plt.plot(
					np.rad2deg(self._grid.vertices_of_vertex.vlon[i]),
					np.rad2deg(self._grid.latitude_vertices.vlat[i]),
					c="k",
					lw=1,
					alpha=0.1,
					transform=transformatio,
				)
			if v6 > 0:
				i = np.array([v, v6])
				plt.plot(
					np.rad2deg(self._grid.vertices_of_vertex.vlon[i]),
					np.rad2deg(self._grid.latitude_vertices.vlat[i]),
					c="k",
					lw=1,
					alpha=0.1,
					transform=transformatio,
				)
			v=v+1
		plt.scatter(
			[float(np.rad2deg(self._grid.vlon[x-1])) for x in vsequence],
			[float(np.rad2deg(self._grid.vlat[x-1])) for x in vsequence],
			c = 'r', s = 15, transform=transformatio
			)

		ll = 0
		for x in vsequence:
			plt.text(float(np.rad2deg(self._grid.vlon[x-1])),
					float(np.rad2deg(self._grid.vlat[x-1])),
					str(ll), transform=transformatio
					)
			ll += 1

		plt.show()
		plt.close()

	def plot_rhomboid_cell(self, rhomboid: Rhomboid, **kwargs):
		pltsize = (100, 80)
		if 'size' in kwargs.keys():
			assert(type(kwargs['size'] == Tuple[int, int]))
			pltsize = kwargs['size']

		with_color = False
		if 'with_color' in kwargs.keys():
			with_color = kwargs['with_color']

		cells = self.get_cells(rhomboid, with_color=with_color)
		#print(len(cells))
		fig = plt.figure(figsize=(30, 20)) # Need to find a way of setting the size right...
		ax = fig.add_subplot(1, 1, 1, projection=ccrs.Mollweide())
		ax.set_global()
		ax.add_feature(cfeature.LAND, zorder=0, edgecolor="black")
		pad = ''
		c = 0
		transformatio = ccrs.Geodetic()
		for v1, v2, v3 in self.grid.vertex_of_cell.values.T - 1:
			i = np.array([v1, v2, v3, v1])
			plt.plot(
					np.rad2deg(self.grid.vertex.vlon[i]),
					np.rad2deg(self.grid.vertex.vlat[i]),
					c="k",
					lw=1,
					alpha=0.1,
					transform=transformatio,
			)
		for v1, v2, v3 in self.grid.vertex_of_cell.values.T[cells] - 1:
			i = np.array([v1, v2, v3, v1])
			plt.plot(
					np.rad2deg(self.grid.vertex.vlon[i]),
					np.rad2deg(self.grid.vertex.vlat[i]),
					c="r",
					lw=3,
					alpha=0.1,
					transform=transformatio,
			)
			ll = 0
			for x in cells:
				plt.text(float(np.rad2deg(self.grid.cell.clon[x])),
						float(np.rad2deg(self.grid.cell.clat[x])),
						str(ll), transform=transformatio
						)
				ll += 1

		plt.show()
		plt.close()

	@property
	def grid(self):
		return self._grid
	
	@property
	def main_path_length(self):
		return self.interesting_path_length
	
	@property
	def paths(self):
		return self._paths
	
	@property
	def pentagons(self):
		return [x+1 for x in self.eov]