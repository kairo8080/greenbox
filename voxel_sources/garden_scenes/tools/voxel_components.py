from collections import deque
def components(points):
 remaining=set(points); result=[]
 while remaining:
  queue=deque([remaining.pop()]); group=set(queue)
  while queue:
   x,y,z=queue.popleft()
   for dx,dy,dz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
    neighbor=(x+dx,y+dy,z+dz)
    if neighbor in remaining:
     remaining.remove(neighbor); queue.append(neighbor); group.add(neighbor)
  result.append(group)
 return sorted(result,key=len,reverse=True)
