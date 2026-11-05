pass                                                                          
import re


def run_solver_replacement(context,recipe):
    pass                                                                      
    import importlib.util
    from pathlib import Path
    import sys
    spec=importlib.util.spec_from_file_location('motion_solver_successor',Path(__file__).with_name('mutacje-solver.py'))
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module.run_replacement(context,recipe)

def function_span(source,name):
    match=re.search(r'^fun '+re.escape(name)+r'\(',source,re.M)
    if not match:raise ValueError('missing product function: '+name)
    start=source.find('{',match.start());depth=0
    if start<0:raise ValueError('function has no body: '+name)
    for index in range(start,len(source)):
        if source[index]=='{':depth+=1
        if source[index]=='}':
            depth-=1
            if depth==0:return match.start(),index+1
    raise ValueError('unterminated product function: '+name)

def apply(source,recipe):
    lo,hi=function_span(source,recipe['scope'])
    block=source[lo:hi]
    for edit in recipe.get('edits',[{'expression':recipe.get('expression'),'replacement':recipe.get('replacement')} ]):
        old,new=edit['expression'],edit['replacement']
        if not old or block.count(old)!=1:
            raise ValueError(recipe['name']+': expected single hit in '+recipe['scope']+': '+repr(old))
        block=block.replace(old,new,1)
    return source[:lo]+block+source[hi:]


def edit_sequence(block,edits):
    pass                                                                         
    hits=[]
    for edit in edits:
        old,new=edit['expression'],edit['replacement']
        count=block.count(old) if old else 0
        hits.append(count)
        if count==1:block=block.replace(old,new,1)
    return block,hits


def recipe_result(source,recipe,*,whole_file=False):
    lo,hi=(0,len(source)) if whole_file else function_span(source,recipe['scope'])
    edits=recipe.get('edits',[{'expression':recipe.get('expression'),'replacement':recipe.get('replacement')}])
    block,hits=edit_sequence(source[lo:hi],edits)
    return source[:lo]+block+source[hi:],hits
