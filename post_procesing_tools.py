#!/usr/bin/python



###
# Date <05.02.2019>
# New features:
#       * Compute_Perturbation that computes 2nd order terms
#       * Compute_KdP2 that computes second order perturbation in Matrix form
#          i.e. H_2
#       * Compute_KdP1 and Compute_H0 have been added to compute fist and zero-th
#          order matrix forms of Hamiltonian (note that Compute_H gives the same
#          matrices and eigenvalues as Compute_H0 + Compute_KdP1
#       * Added Compute_Perturbation_mat for members of product in KdP2
###
# Date <11.01.2019>
# New features:
#       * Gather_Symmetries is now more generalized: it can read any filename 
#       * Added function Gather_Matrices that gathers full matrices or irrep
#       * Added function Compute_small_r that makes preparations for unitary 
#        transform
#       * Added fucntion Gather_Unitary_Transforms that gathers unitary
#       transforms that relate two equivalent irreps
#
###
###
# Date <17.12.2018>
# New features:
#        * Added functions Gather_Charachters, Gather_Degeneracies and char_coef
###
# Date <13.12.2018.>
# New features:
#        * Added Symmetry class and Gather_Symmetries function 
###
###
# Date <03.12.2018.>
# New features: 
#       * Added 'units' option for Gather_E (Rydberg,Hartree or Electronvolt)
#       * Gather_E and Gather_K now load from index.xml file
#       * Added Calculate_H function that calculates k dot p Hamiltonian
#           in 1st order of effective mass method                    
###
# Date <28.11.2018.>
# New features: Added 'details' option. Set details to true for more info
###



import numpy as np
import re as re
import numpy.linalg as nplin

def Gather_C(path,k_point,details=False):    
    FILE = open (path+'/wfc.{}'.format(k_point),"r")
    nbnd=0
    igwx=0
    WF=[]
    if details:
        print("Now performing for k-point={}:\n".format(k_point))
    for line in FILE:
        if 'Info' in line:
            found_nbnd = re.search('nbnd="(.+?)"',line)
            if found_nbnd:
                nbnd = int(found_nbnd.group(1))
        if 'igwx' in line:
            found_igwx=re.search('igwx="(.+?)"',line)
            if found_igwx:
                igwx = int(found_igwx.group(1))
        for n in range(nbnd):
            wf_n=[]
            if '<Wfc.{} type='.format(n+1) in line:
                for i in range(igwx):
                    nextLine=next(FILE)
                    A = (nextLine.replace("\n","")).split(",")
                    C = complex(float(A[0]),float(A[1]))
                    wf_n.append(C)
                WF.append(wf_n)
    if details:
        print("\tReading wave-fuctions: DONE")
    WF=np.array(WF)
    return WF

def Gather_G(path,k_point,details=False):
    FILE = open (path+'/grid.{}'.format(k_point),"r")
    size=0
    GV=[]
    if details:
        print("Gathering G-vectors for k-point={}:\n".format(k_point))
    for line in FILE:
        if '<grid type=' in line:
            size = re.search('size="(.+?)"',line)
            if size:
                size = int(int(size.group(1))/3)
            for i in range(size):
                nextLine=next(FILE)
                g = (nextLine.replace("\n","")).split()
                G_i = [int(g[0]),int(g[1]),int(g[2])]
                GV.append(G_i)
    if details:
        print("\tReading G-vectors: DONE")
    GV=np.array(GV)
    return GV

def Gather_K(path,details=False):
    FILE = open (path+'/index.xml',"r")
    KV=[]
    if details:
        print("Gathering K-vectors...\n")
    for line in FILE:
        if '<Kmesh' in line:
            found_nk = re.search('nk="(.+?)"',line)
            if found_nk:
                nk = int(found_nk.group(1))
        if '<k type=' in line:
            for k in range(nk):
                nextLine=next(FILE)
                k = nextLine.split()
                k_i = [float(k[0]),float(k[1]),float(k[2])]
                KV.append(k_i)
    if details:
        print("\tGathering K-vectors: DONE")
    KV=np.array(KV)
    return KV

def Gather_E(path,details=False,units='Hartree',Fermi_norm=True):
    FILE = open (path+'/index.xml',"r")
    nbnd=0
    nk=0
    fermi=0
    E=[]
    if details:
        print("Now performing for k-point={}:\n".format(k_point))
    for line in FILE:
        if '<Eigenvalues' in line:
            found_nk = re.search('nk="(.+?)"',line)
            if found_nk:
                nk = int(found_nk.group(1))
            found_nbnd = re.search('nbnd="(.+?)"',line)
            if found_nbnd:
                nbnd = int(found_nbnd.group(1))
            found_fermi = re.search('efermi="(.+?)"',line)
            if found_fermi:
                fermi = float(found_fermi.group(1))            
        for k in range(1,nk+1):
            E_k=[]
            if '<e.{} type='.format(k) in line:
                for n in range(nbnd):
                    nextLine=next(FILE)
                    e = float(nextLine)
                    if Fermi_norm:
                        e = e - fermi
                    E_k.append(e)
                E.append(E_k)
    if details:
        print("\tReading wave-fuctions: DONE")
    E=np.array(E)
    if units=='Hartree':
        return E*0.5
    if units=='Electronvolt':
        return E*13.605698066
    if units=='Rydberg':
        return E


def Check_Orthonormality(WF, tol=1e-13,details=False):
    # check orthonormality
    nbnd = len(WF)
    Ort_MAT=np.zeros((nbnd,nbnd),dtype=complex)
    for i in range(nbnd):
        for j in range(i,nbnd):
            A=np.array(WF[i])
            B=np.array(WF[j])
            Ort_MAT[i][j]=np.vdot(A,B)
            Ort_MAT[j][i]=Ort_MAT[i][j]
    if details:
        print("\tVector product is: DONE")
    
    orthonormal=True
    #print("\nDiagonal elements:\n")
    tol_global=tol
    index = [0,0]
    for i in range(nbnd):
        if abs(abs(Ort_MAT[i][i])-1.0)<tol:
            pass#print (1)
        else:
            if details:
                print ("\n\tMatrix element [{},{}] is:{}".format(i,i,Ort_MAT[i][i]))
            orthonormal=False
            ort_new=False
            tol_new=tol
            while ort_new==False:
                    tol_new=tol_new*10
                    if tol_global<tol_new: tol_global=tol_new; index=[i,i]
                    if abs(abs(Ort_MAT[i][i])-1.0)<tol_new:
                        if details:
                            print("\tTolerance for {}".format(tol_new))
                        ort_new=True
    #print("\nOff-diagonal elements:\n")
    for i in range(nbnd):
        for j in range(i+1,nbnd):
            if abs(Ort_MAT[i][j])<tol:
                pass#print(0)
            else:
                if details:
                    print ("\n\tMatrix element: {},{} is:{}".format(i,j,abs(Ort_MAT[i][j])))
                orthonormal=False
                ort_new=False
                tol_new=tol
                while ort_new==False:
                    tol_new=tol_new*10
                    if tol_global<tol_new: tol_global=tol_new; index=[i,j]
                    if abs(Ort_MAT[i][j])<tol_new:
                        if details: 
                            print("\tTolerance for {}".format(tol_new))
                        ort_new=True                    
    print('\nOrthonormality {} for tolerance {}'.format(orthonormal,tol))
    if not orthonormal:
        print('Orthonormal for tolerance {} in index {}\n'.format(tol_global,index))       
        
def Compute_Matrix_Element(G_vec,C_terms,m,n):
    A = np.array(C_terms[m])
    B = np.array(C_terms[n])
    Gx=G_vec[:,0]
    Gy=G_vec[:,1]
    Gz=G_vec[:,2]
    G = [np.vdot(A,Gx*B),np.vdot(A,Gy*B),np.vdot(A,Gz*B)]
    return np.array(G)  

def Compute_H(k_mesh,k_point,E_k,
              G_space,C_terms,a,
              units='Hartree',
              details=False):
    uni=['Hartree',1.0]
    if units=='Rydberg':
        uni=['Rydberg',2.0]
    if units=='Electronvolt':
        uni=['Electronvolt',27.211396132]
    tpiba = 2*np.pi/a
    tpiba2=tpiba**2
    kR2= np.dot(k_point,k_point)
    H=[]
    for k_i in range(len(k_mesh)):
        k2 = np.dot(k_mesh[k_i],k_mesh[k_i])
        kkR = k_mesh[k_i]-k_point
        H_i = np.zeros((len(C_terms),len(C_terms)),dtype=complex)
        for m in range(len(C_terms)):
            for n in range(len(C_terms)):
                CGC = Compute_Matrix_Element(G_space,C_terms,m,n)
                KdP = np.dot(kkR,CGC)
                if m==n:
                    H_i[m][m] = E_k[m] + 0.5*tpiba2*(k2-kR2) + tpiba2*KdP
                else:
                    H_i[m][n] = tpiba2*KdP
        H_i = (np.linalg.eigvalsh(H_i))
        H.append(H_i)
        if details:
            print("eigenvalues of H_{} in units of {}".format(k_i+1,uni[0]))
            print((H_i)*uni[1])
    print('Calculating bands: DONE')
    return np.array(H)*uni[1]

class Symmetry:
    def __init__(self, matrix, operation):
        self.matrix = matrix
        self.operation = operation
        self.char = np.trace(matrix)
    def __str__(self):
        return '{} {}\n'.format(self.matrix,self.operation)
    def __repr__(self):
        return '{} {}\n'.format(self.matrix,self.operation)
        
def Gather_Symmetries(path,file_name="index.xml"):
    full_path=path+"/"+file_name
    FILE = open (full_path,"r")
    n_sym=0
    inv_sym = False
    sym_list=[]
    for line in FILE:
        if '<symmops' in line:
            n_sym = re.search('nsym="(.+?)"',line)
            if n_sym:
                n_sym = int(n_sym.group(1))
    for i in range(1,n_sym+1):
        FILE = open (full_path,"r")
        for line in FILE:
            if '<info.{} name'.format(i) in line:
                sym_name = re.search('name="(.+?)"',line)
                sym_name = str(sym_name.group(1))
                nextLine=next(FILE)
                mat_type = re.search('type="(.+?)"',nextLine)
                nextLine=next(FILE)
                r = nextLine.split()
                R1 = [int(r[0]),int(r[1]),int(r[2])]
                nextLine=next(FILE)
                r = nextLine.split()
                R2 = [int(r[0]),int(r[1]),int(r[2])]
                nextLine=next(FILE)
                r = nextLine.split()
                R3 = [int(r[0]),int(r[1]),int(r[2])]
                mat = np.array([R1,R2,R3])
                R = Symmetry(mat,sym_name)
                sym_list.append(R)
    return sym_list

def char_coef(g_ired,g_red,Nk):
    prod=0
    for i in range(len(Nk)):
        prod+=g_ired[i]*g_red[i]*Nk[i]
    return prod/sum(Nk)

def red_to_irreds(char_red,irred_list,Nk,present='list'):
    irreds = []
    for char_g in irred_list:
        c=char_coef(char_g[0],char_red,Nk)
        if abs(c)>1e-3:
            if present=='list': irreds.append([char_g[1],c])
            if present=='print':print(char_g[1],c)
    if present=='list': return irreds

def Gather_Degeneracies(E_list,functions=False):
    deg_e=[]
    deg_u=[]
    index=0
    while index+3<E_list.shape[0]:
        if abs(E_list[index]-E_list[index+1])<1e-4:
            index += 1
            if abs(E_list[index]-E_list[index+1])<1e-4:
                index += 1
                deg_e.append([E_list[index],3,'index: {}-{}'.format(index-2,index)])
                deg_u.append([index-2,index-1,index])
            else:
                deg_e.append([E_list[index],2,'index: {}-{}'.format(index-1,index)])
                deg_u.append([index-1,index])
        else:
            deg_e.append([E_list[index],1,'index: {}'.format(index)])
            deg_u.append([index])
        index +=1
    if functions==False:
        return np.array(deg_e)
    else:
        return (deg_u),np.array(deg_e)

def Gather_Charachters(k_start,k_stop,symmetry_list,G_R,C_R,k_Rpoint,details=False):
    charachters=[]
    dim_G = 2*abs(max(np.amax(G_R),np.amin(G_R),key=abs))+1
    if details: print('Dimension of 3x3x3 square matrix is:', dim_G)
    M=np.zeros((dim_G,dim_G,dim_G),dtype=int)
    if details: print('Creating G-matrix')
    for i in range(len(G_R)):
        n1,n2,n3 = G_R[i,0],G_R[i,1],G_R[i,2]
    #    print(n1,n2,n3, i)
        M[n1,n2,n3] = i
    if details: print('G-matrix: Done')

    for s in [0, 1, 6, 4, 16, 24, 25, 30, 28, 40]:
        sym_name=symmetry_list[s].operation
        sym_matrix=symmetry_list[s].matrix
        if details: print('\nNow performing for '+ sym_name)
        char=0
        for k in range(k_start,k_stop+1):
            RC_R = np.zeros(len(G_R),dtype=complex)
            for i in range(len(G_R)):
                g_i = np.matmul(sym_matrix,G_R[i]+k_Rpoint)-k_Rpoint
                n1,n2,n3=int(g_i[0]),int(g_i[1]),int(g_i[2])
                index = M[n1,n2,n3]
                RC_R[i] = C_R[k,index]
            char += np.vdot(RC_R,C_R[k])
        if details: print('charachter = ',char)
        charachters.append([int(round(char.real)), sym_name])
    if details: print('Done')
    return np.array(charachters)

def Gather_Matrices(k_start,k_stop,symmetry_list,G_R,C_R,k_Rpoint,details=False):
    Matrices=[]
    dim_G = 2*abs(max(np.amax(G_R),np.amin(G_R),key=abs))+1
    if details: print('Dimension of 3x3x3 square matrix is:', dim_G)
    M=np.zeros((dim_G,dim_G,dim_G),dtype=int)
    if details: print('Creating G-matrix')
    for i in range(len(G_R)):
        n1,n2,n3 = G_R[i,0],G_R[i,1],G_R[i,2]
    #    print(n1,n2,n3, i)
        M[n1,n2,n3] = i
    if details: print('G-matrix: Done')

    for s in range(len(symmetry_list)):
        sym_name=symmetry_list[s].operation
        sym_matrix=symmetry_list[s].matrix
        if details: print('\nNow performing for '+ sym_name)
        dim = k_stop-k_start+1
        full_mat=np.zeros((dim,dim),dtype=complex)
        for m in range(k_start,k_stop+1):
            RC_R = np.zeros(len(G_R),dtype=complex)
            for i in range(len(G_R)):
                g_i = np.matmul(sym_matrix,G_R[i]+k_Rpoint)-k_Rpoint
                n1,n2,n3=int(g_i[0]),int(g_i[1]),int(g_i[2])
                index = M[n1,n2,n3]
                RC_R[i] = C_R[m,index]
            for n in range(k_start,k_stop+1):
                mat_comp=np.vdot(RC_R,C_R[n])
                full_mat[m-k_start,n-k_start]= (mat_comp)
        if details: print('Matrix = \n',full_mat,'\nSym. Matrix =\n',sym_matrix)
        Matrices.append(Symmetry(full_mat,sym_name))
        #Matrices.append([full_mat, sym_name,np.trace(full_mat)])
    if details: print('Done')
    return np.array(Matrices)

def Compute_small_r(sym_table,sym_wf):
    if len(sym_table)!=len(sym_wf):
        raise ValueError("Irreps are not compatible")
    order=len(sym_table)
    dim = len(sym_table[0].matrix)
    r = np.zeros((dim,dim),dtype=complex)
    sq = np.sqrt(dim/order)
    for i in range(dim):
        for j in range(dim):
            s = 0+0j
            for g in range(order):
                s1 = 0+0j
                s1 = sym_table[g].matrix[i,i]*nplin.inv(sym_wf[g].matrix)[j,j]
                s += s1
            r[i,j] = np.sqrt(s)
    return sq*r
    #else: print("Error: Representations are not of the same order!")

def Gather_Unitary_Transforms(r,sym_table,sym_wf):
    if len(sym_table)!=len(sym_wf):
        raise ValueError("Irreps are not compatible")
    dim = len(r)
    order=len(sym_table)
    great_u = []
    for m in range(dim):
        g_u=[]
        for n in range(dim):
            g_u.append(0)
        great_u.append(g_u)
    factor=dim/order
    for a in range(dim):
        for b in range(dim):
            if abs(r[a,b])>1e-14:
                small_u = np.zeros((dim,dim),dtype=complex)
                for i in range(dim):
                    for j in range(dim):
                        u_ij=0+0j
                        for g in range(order):
                            u1 = nplin.inv(sym_wf[g].matrix)[i,a]*sym_table[g].matrix[b,j]
                            u_ij += u1
                        small_u[i,j]=factor/r[a,b] *u_ij
                great_u[a][b]=np.array(small_u)
            else: 
                great_u[a][b]=0
    return np.array(great_u)


def Compute_Perturbation(G_vec,C_terms,ext_basis,E_terms,E_ext,kkr,m,n):
        new_basis = np.vstack((ext_basis,C_terms))
        dim = len(ext_basis)
        cgc = 0
        Eavg = (E_terms[m]+E_terms[n])/2
        for l in range(len(E_ext)):
            delta_E1 =1/(Eavg - E_ext[l])
            kpi = np.dot(kkr,Compute_Matrix_Element(G_vec,new_basis,dim+m,l))
            kpj = np.dot(kkr,Compute_Matrix_Element(G_vec,new_basis,l,dim+n))
            cgc += kpi*kpj*delta_E1
        return cgc
    
def Compute_KdP2(k_mesh,k_point,E_k,E_ext,G_space,C_terms,ext_basis,a,units='Hartree',details=False):
    uni=['Hartree',1.0]
    if units=='Rydberg':
        uni=['Rydberg',2.0]
    if units=='Electronvolt':
        uni=['Electronvolt',27.211396132]
    tpiba = 2*np.pi/a
    tpiba2=tpiba**2
    tpiba4=tpiba2**2
    H=[]
    H_eig=[]
    dim = len(C_terms)
    for k_i in range(len(k_mesh)):
        k2 = np.dot(k_mesh[k_i],k_mesh[k_i])
        kkR = k_mesh[k_i]-k_point
        H_i = np.zeros((dim,dim),dtype=complex)
        for m in range(len(C_terms)):
            for n in range(len(C_terms)):
                KdP2 = Compute_Perturbation(G_space,C_terms,ext_basis,E_k,E_ext,kkR,m,n)
                H_i[m][n] = tpiba4*KdP2
        H_i_eig = (np.linalg.eigvalsh(H_i))
        H.append(H_i)
        H_eig.append(H_i_eig)
        if details:
            print("eigenvalues of KdP2_{} in units of {}".format(k_i+1,uni[0]))
            print((H_i_eig)*uni[1])
    print('Calculating KdP2: DONE')
    return np.array(H)*uni[1], np.array(H_eig)*uni[1]

def Compute_KdP1(k_mesh,k_point,G_space,C_terms,a,units='Hartree',details=False):
    uni=['Hartree',1.0]
    if units=='Rydberg':
        uni=['Rydberg',2.0]
    if units=='Electronvolt':
        uni=['Electronvolt',27.211396132]
    tpiba = 2*np.pi/a
    tpiba2=tpiba**2
    tpiba4=tpiba2**2
    H=[]
    H_eig=[]
    dim = len(C_terms)
    for k_i in range(len(k_mesh)):
        kkR = k_mesh[k_i]-k_point
        H_i = np.zeros((dim,dim),dtype=complex)
        for m in range(len(C_terms)):
            for n in range(len(C_terms)):
                KdP = Compute_Matrix_Element(G_space,C_terms,m,n)
                H_i[m][n] = tpiba2*kkR.dot(KdP)
        H_i_eig = (np.linalg.eigvalsh(H_i))
        H.append(H_i)
        H_eig.append(H_i_eig)
        if details:
            print("eigenvalues of KdP_{} in units of {}".format(k_i+1,uni[0]))
            print((H_i_eig)*uni[1])
    print('Calculating KdP: DONE')
    return np.array(H)*uni[1], np.array(H_eig)*uni[1]

def Compute_H0(k_mesh,k_point,E_k,a,units='Hartree',details=False):
    uni=['Hartree',1.0]
    if units=='Rydberg':
        uni=['Rydberg',2.0]
    if units=='Electronvolt':
        uni=['Electronvolt',27.211396132]
    tpiba = 2*np.pi/a
    tpiba2=tpiba**2
    H=[]
    H_eig=[]
    dim = len(E_k)
    for k_i in range(len(k_mesh)):
        kkR2 = k_mesh[k_i].dot(k_mesh[k_i])-k_point.dot(k_point)
        H_i = np.zeros((dim,dim),dtype=complex)
        for m in range(dim):
                H_i[m][m] = E_k[m] + 0.5*tpiba2*kkR2
        H_i_eig = (np.linalg.eigvalsh(H_i))
        H.append(H_i)
        H_eig.append(H_i_eig)
        if details:
            print("eigenvalues of KdP_{} in units of {}".format(k_i+1,uni[0]))
            print((H_i_eig)*uni[1])
    print('Calculating H0: DONE')
    return np.array(H)*uni[1], np.array(H_eig)*uni[1]

def Compute_Perturbation_mat(G_vec,C_terms,ext_basis,E_terms,E_ext,m,n):
        new_basis = np.vstack((ext_basis,C_terms))
        dim = len(ext_basis)
        cgc = 0
        mat = np.zeros((3,3),dtype=complex)
        Eavg = (E_terms[m]+E_terms[n])/2
        for l in range(len(ext_basis)):
            delta_E1 =1/(Eavg - E_ext[l])
            kpi = Compute_Matrix_Element(G_vec,new_basis,dim+m,l)
            kpj = Compute_Matrix_Element(G_vec,new_basis,l,dim+n)
            for i in range(3):
                for j in range(3):
                    mat[i,j] += kpi[i]*kpj[j]*delta_E1
        return mat