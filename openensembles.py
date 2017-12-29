"""
OpenEnsembles is a resource for performing and analyzing ensemble clustering

Copyright (C) 2017 Naegle Lab

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import numpy as np 
import pandas as pd 
import sklearn.cluster as skc
import matplotlib.pyplot as plt
import scipy.cluster.hierarchy as sch
from sklearn import preprocessing
import transforms as tx
import clustering_algorithms as ca 
import finishing as finish
import cooccurrence as co
import validation as val
import warnings
from random import randint
import openensembles as oe
from mpl_toolkits.mplot3d import Axes3D

class data:
    """
    df is a dataframe and x is the x_axis values (or numbers indicating the
    number entry)

    Parameters
    -----------
    df : a pandas dataframe 
        Dataframe with objects in rows and columns representing the feature dimensions

    x : list
        The x-axis elements. If x is a list of strings, it will be converted here to a list of ints (range 0 to len(x))
    
    Attributes
    -----------
    df : pandas dataframe 
        the original dataframe

    D : dictionary 
        A dictionary of data matrices, callable by 'source_name'

    x : list 
        a list of integer or float values

    x_labels : list
        a list of strings (if that was passed in) or the int and float. So that xticklabels could be updated or referenced

    Raises
    --------
    ValueError of the size of x and dimensionality of df do not match
    """
    def __init__(self, df, x):

        self.df = df
        self.D = {}
        self.x = {}
        self.params = {}

        self.D['parent'] = np.asarray(df)

         #check that the number of x-values matches the array
        if(len(x) != self.D['parent'].shape[1]):
            raise ValueError("ERROR: Size of x-values (%d) does not match that of of the dataframe dimensions (%d), replacing with an vector of integers of correct size"%(len(x), self.D['parent'].shape[1]))

        errors = False
        for val in x:
            if not isinstance(val, int) and not isinstance(val, float):
                errors = True
        if errors:
            #warnings.warn("Changing string list of x into an integer in the same order as string list, starting with 0")
            xVals = list(range(0,len(x)))
            self.x_labels = x

        else: 
            xVals = x
            self.x_labels = x


        self.x['parent'] = xVals
        self.params['parent'] = []

       
    def transforms_available(self):
        """
        Returns a list of all transformations available
        """
        txfm = tx.transforms(self.x, self.D, {})
        TXFM_FCN_DICT = txfm.transforms_available()
        return TXFM_FCN_DICT

    def plot_data(self, source_name, fig_num=1, **kwargs):
        """ Plot the data matrix that belongs to source_name
            
            Parameters
            -----------
            
            source_name : string
                name of data source to plot, e.g. 'parent'
            fig_num: int
                Set to a different figure number to plot on existing figure. Default fig_num=1
            **class_labels : list of ints
                this is a vector that assigns points to classes, and will be used to color the points according to assigned class type
            **clusters_to_plot: list of ints
                If you wish to plot a subset of cluster types (classes), pass that as a list of ints
            **title : string
                Title for plot

            Raises
            ------
            ValueError: 
                If clusters_to_plot not a set in cluster labels

        """
        m = self.D[source_name].shape[0] 
        n = self.D[source_name].shape[1]
        if 'title' in kwargs:
            title = kwargs['title']
        else:
            title = ''
        if 'class_labels' not in kwargs:
            class_labels = np.ones(m)
        else:
            class_labels = kwargs['class_labels']
        if 'clusters_to_plot' not in kwargs:
            clusters = np.unique(class_labels)
        else:
            #check, this argument should be a list with a direct set match
            clustersPossible = np.unique(class_labels)
            clusters = kwargs['clusters_to_plot']
            if not set(clusters) < set(clustersPossible):
                raise ValueError("ERROR: the clusters to plot are not a direct match to possible clusters in plot_data")



        #clusters = np.unique(class_labels)

        color=iter(plt.cm.rainbow(np.linspace(0,1,len(clusters))))
        
        fig = plt.figure(fig_num, figsize=(6, 6))
        #plt.hold(True)

        #SETUP axes, as either 2D or 3D
        if n==3:
            ax = fig.gca(projection='3d')
        else:
            ax = fig.add_subplot(111)
        #ax.hold(True)

        if n <= 3: #scatter plots for less than 4-dimensions
            for clusterNum in clusters:
                indexes = np.where(class_labels==clusterNum)
                if n==2:
                    plt.scatter(self.D[source_name][indexes,0], self.D[source_name][indexes,1], c=next(color))
                elif n==3:
                    ax.scatter(self.D[source_name][indexes,0], self.D[source_name][indexes,1], self.D[source_name][indexes,2], c=next(color), s=10)


            plt.xlabel(self.x[source_name][0])
            plt.ylabel(self.x[source_name][1])
            if n==3:
                ax.set_zlabel(self.x[source_name][2])

        else:
            plt.hold(True)
            ax.hold(True)
            for clusterNum in clusters:
                indexes = np.where(class_labels==clusterNum)
                plt.plot(self.x[source_name], self.D[source_name][indexes].transpose(), c=next(color))


        plt.title(title)
        #plt.show()
        return fig





    def transform(self, source_name, txfm_fcn, txfm_name, **kwargs):
        """
        This runs transform (txfm_fcn) on the data matrix defined by
        source_name with parameters that are variable for each transform. 
        For example, oe.data.transform('parent', 'zscore','zscore_parent', axis=0) will run the
        zscore in a vector-wise manner across the matrix (column-wise) and the new data
        dictionary access to the transformed data is oe.data['zscore_parent']
        Successful completion results in
        the addition of a new entry in the data dictionary with a key according
        to txfm_name.

        Parameters
        ----------
        source_name: string
            the name of the source data, for example 'parent', or 'log2'
        txfm_fcn: string
            the name of the transform function. See transforms.py or run oe.data.transforms_available() for list
        txfm_name: string
            the name you want to use in the data object dictionary oe.data.D['name'] to access transformed data

        Other Parameters
        ----------------
        **Keep_NaN: boolean
            Set to True in order to prevent transformations from being added that produce NaNs. 
            Default Keep_NaN=True this will add transformed data even if NaNs are produced. Set to 0 to prevent addition of data transforms containing NaNs.
        **Keep_Inf: boolean
            Set to True in order to prevent transformations from being added that produce infinite values
            Default: Keep_Inf = True (this will add transformed data even if infinite values are produced. Set to 0 to prevent addition of data transforms conta

        Warnings
        --------
        NaNs or infinite values are produced

        Raises
        ------
        ValueError
            if the transform function does not exist OR if the data source does not exist by source_name

        Examples
        --------
        >>> import pandas as pd
        >>> import openensembles as oe
        >>> df = pd.read_csv(file)
        >>> d = oe.data(df, df.columns
        >>> d.transform('parent', 'zscore', 'zscore')
        >>> d.transform('zscore', 'PCA', 'pca', n_components=3)

        
        """
        #CHECK that the source exists
        if source_name not in self.D:
            raise ValueError("ERROR: the source you requested for transformation does not exist by that name %s"%(source_name))
        TXFM_FCN_DICT = self.transforms_available()
        Keep_NaN_txfm = 1 #default value is to keep a transform, even if NaN values are created
        Keep_Inf_txfm = 1 #default value is to keep a transform, even if NaN values are created
        paramDict = {}

        if not kwargs:
            var_params = []
        else:
            var_params = kwargs
            if 'Keep_NaN' in kwargs:
                Keep_NaN_txfm = kwargs['Keep_NaN']
            if 'Keep_Inf' in kwargs:
                Keep_Inf_txfm = kwargs['Keep_Inf']

        ######BEGIN TXFM BLOCK  ######
        if txfm_fcn not in TXFM_FCN_DICT:
            raise ValueError( "The transform function you requested does not exist, currently the following are supported %s"%(list(TXFM_FCN_DICT.keys())))

        txfm = tx.transforms(self.x[source_name], self.D[source_name], kwargs)
        func = getattr(txfm,txfm_fcn)
        func()
 
        #### FINAL staging, X, D and var_params have been set in transform block, now add each
        #check and print a warning if NaN values were created in the transformation
        
        boolCheck = np.isnan(txfm.data_out)
        numNaNs = sum(sum(boolCheck))
        if numNaNs:
            warnings.warn("WARNING: transformation %s resulted in %d NaN values"%(txfm_fcn, numNaNs), UserWarning) 
            if not Keep_NaN_txfm:
                print("Transformation %s resulted in %d NaN values, and you requested not to keep a transformation with NaNs"%(txfm_fcn, numNaNs)) 
                return
        infCheck = np.isinf(txfm.data_out)
        numInf = sum(sum(infCheck))
        if numInf > 0:
            warnings.warn("WARNING: transformation %s resulted in %d Inf values"%(txfm_fcn, numInf), UserWarning) 
            if not Keep_Inf_txfm:
                #print("Transformation %s resulted in %d Inf values, and you requested not to keep a transformation with infinite values"%(txfm_fcn, numInf)) 
                return

        self.x[txfm_name] = txfm.x_out 
        self.params[txfm_name] = txfm.var_params
        self.D[txfm_name] = txfm.data_out

class cluster:
    """
    Initialize a clustering object, which is instantiated with a data object class from OpenEnsembles
    When clustering is performed, the dictionaries of all attributes are extended using the key given as output_name
    
    Parameters
    ----------
    dataObj
        openensembles.data class -- consists at least of one data matrix called 'parent'
    
    Returns
    -------
    clusterObject
        empty openensembles.cluster object 

    Attributes
    ----------
    dataObj: openensembles.data class
        openensembles.data class that was used to instantiate cluster object
    labels: dict of lists
        A dictionary of lists of clustering solutions (ints). Referred to as output_name in .cluster method
    data_source: dict of strings
        Name of data source in dataObj
    params: dict of dicts
        A dictionary of all parameters passed during clustering
    clusterNumbers: dict of lists
        A listing of the unique set of cluster numbers produced in a clustering 

    Examples
    --------
    Load data, zscore it, transform it into the first three principal components and cluster using KMeans with K=4

    >>> import pandas as pd
    >>> import openensembles as oe
    >>> df = pd.read_csv(file)
    >>> d = oe.data(df, df.columns
    >>> d.transform('parent', 'zscore', 'zscore')
    >>> d.transform('zscore', 'PCA', 'pca', n_components=3)
    >>> c = oe.cluster(d)
    >>> c.cluster('pca', 'kmeans', 'kmeans_pca', 4)

    """
    def __init__(self, dataObj):
        self.dataObj = dataObj 
        self.labels= {} #key here is the name like HC_parent for hierarchically clustered parent
        self.data_source = {} # keep track of the key to the data source in object used
        self.params = {} # keep track of the parameters used (includes random seed)
        self.algorithms = {} #keep track of the algorithm used
        self.clusterNumbers = {}

    def algorithms_available(self):
        """ 
        Call this to list all algorithms currently available in algorithms.py
        """
        algorithms = ca.clustering_algorithms(self.dataObj.D['parent'], {})
        ALG_FCN_DICT = algorithms.clustering_algorithms_available()
        return ALG_FCN_DICT

    def cluster(self, source_name, algorithm, output_name, K=None, Require_Unique=False, **kwargs):

        """
        This runs clustering algorithms on the data matrix defined by
        source_name with parameters that are variable for each algorithm. Note that K is 
        required for most algorithms. 
        
        Parameters
        ----------
        source_name: string
            the source data matrix name to operate on in clusterclass dataObj
        algorithm: string
            name of the algorithm to use, see clustering.py or call oe.cluster.algorithms_available()
        output_name: string
            this is the dict key for interacting with the results of this clustering solution in any of the cluster class dictionary attributes
        K: int
            number of clusters to create (ignored for algorithms that define K during clustering). The var_params gets K after, either the parameter passed, or the number of clusters produced
            if the K was not passed.
        Require_Unique: bool
            If FALSE and you already have an output_name solution, this will append a number to create a unique name. If TRUE and a 
            solution by that name exists, this will not add solution and raise ValueError. Default Require_Unique=False

        Warnings
        --------
        This will warn if the number of clusters is differen than what was requested, typically when an algorithm does not accept K as an argument.

        Raises
        ------
            ValueError
                if data source is not available by source_name 

        Examples
        --------
        Cluster using KMeans on parent data

        >>> c = oe.cluster
        >>> c.cluster('parent', 'kmeans','kmeans_parent', K=5) 

        Form an iteration to build an ensemble using different values for K

        >>> for k in range(2,12):
        >>>     name='kmeans_'+k
        >>>     c.cluster('parent', 'kmeans', name, k)

        
        """
        #CHECK that the source exists
        if source_name not in self.dataObj.D:
            raise ValueError("ERROR: the source you requested for clustering does not exist by that name %s"%(source_name))
        ALG_FCN_DICT = self.algorithms_available()
        paramDict = {}

        if not kwargs:
            var_params = {} 
        else:
            var_params = kwargs
        
        ##### Check to see if the same name exists for clustering solution name and decide what to do according to Require_Unique
        if output_name in list(self.labels.keys()):
            if Require_Unique:
                warnings.warn('The name of the clustering solution is redundant and you required unique, solution will not be added')
                return
            else:
                test_name = "%s_%d"%(output_name, randint(0,10000))
                while test_name in self.labels:
                    test_name = "%s_%d"%(output_name, randint(0,10000))
                output_name = test_name
                warnings.warn('For uniqueness, altered output_name to be %s'%(output_name), UserWarning)

        ######BEGIN CLUSTERING BLOCK  ######
        if algorithm not in ALG_FCN_DICT:
            raise ValueError( "The algorithm you requested does not exist, currently the following are supported %s"%(list(ALG_FCN_DICT.keys())))


        c = ca.clustering_algorithms(self.dataObj.D[source_name], var_params, K)
        func = getattr(c,algorithm)
        func()
 
        #### FINAL staging, c now contains a finished assignment and c.params has final parameters used.

        # CHECK that K is as requested 
        uniqueClusters = np.unique(c.out)
        if K: #check if K was overwritten
            c.var_params['K'] = K
            if len(uniqueClusters) != K:
                warnings.warn("Number of unique clusters %d returned does not match number requested %d for solution: %s"%(len(uniqueClusters), K, output_name), UserWarning)
        else:
            c.var_params['K'] = len(uniqueClusters)


        self.labels[output_name] = c.out
        self.data_source[output_name] = source_name
        self.params[output_name] = c.var_params
        self.clusterNumbers[output_name] = uniqueClusters
        self.algorithms[output_name] = algorithm

    def co_occurrence_matrix(self, data_source_name='parent'):
        """
        Calculate the co-occurrence of all pairs of objects across the ensemble 

        Parameters:
        data_source_name: string
            Name of the data source to link to co-occurrence object. Default is 'parent'

        Returns
        -------
        coMat class
            coMat.co_matrix is the NxN matrix, whose entries indicate the number of times the pair of objects in positon (i,j) cluster across the ensemble
            of clustering solutions available in clustering object. 

        Examples
        --------
        >>> coMat = c.co_occurrence_matrix()
        >>> coMat.plot()

      """
        coMat = co.coMat(self, data_source_name)
        return coMat


    def mixture_model(self, K=2, iterations=10):
        """
        Finishing Technique to assemble a final, hard parition of the data according to maximizing the likelihood according to the
        observed clustering solutions across the ensemble. This will operate on all clustering solutions contained in the container cluster class.
        Operates on entire ensemble of clustering solutions in self, to create a mixture model
        See finishing.mixture_model for more details. 

        Parameters
        ----------
        K: int
            number of clusters to create. Default K=2
        iterations: int
            number of iterations of EM algorithm to perform. Default iterations=10
       
        Returns
        -------
        c: openensembles clustering object
            a new clustering object with c.labels['mixture_model'] set to the final solution. 

        Raises
        ------
            ValueError:
                If there are not at least two clustering solutions

        References
        ----------
        Topchy, Jain, and Punch, "A mixture model for clustering ensembles Proc. SIAM Int. Conf. Data Mining (2004)"
        
        Examples
        --------
        >>> cMM = c.mixture_model(4, 10)
        >>> d.plot_data('parent', cluster_labels=cMM.labels['mixture_model'])

        """
        params = {}
        params['iterations'] = iterations
        params['K'] = K

        #check to make sure more than one solution exists in ensemble
        if len(self.params) < 2:
            raise ValueError("Mixture Model is a finsihing technique for an ensemble, the cluster object must contain more than one solution")
        N = self.dataObj.D['parent'].shape[0]
        parg = []
        for solution in self.labels:
            parg.append(self.labels[solution])

        mixtureObj = finish.mixture_model(parg, N, nEnsCluster=K, iterations=iterations)
        mixtureObj.emProcess()
        c = oe.cluster(self.dataObj)
        name = 'mixture_model'
        c.labels[name] = mixtureObj.labels
        c.data_source[name] = 'parent'
        c.clusterNumbers[name] = np.unique(c.labels[name])
        c.params[name] = params
        c.algorithms[name] = 'mixture_model'
        return c

    def finish_co_occ_linkage(self, threshold, linkage='average'):
        """
        The finishing technique that calculates a co-occurrence matrix on all cluster solutions in the ensemble and 
        then hierarchically clusters the co-occurrence, treating it as a similarity matrix. The clusters are defined by 
        the threshold of the distance used to cut. 



        Parameters
        ----------
        threshold: float
            Linkage distance to use as a cutoff to create partitions
        linkage: string
            Linkage type. See `scipy.cluster.hierarchy <https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html#scipy.cluster.hierarchy.linkage>`_

        Returns
        -------
        c: openensembles clustering object
            a new clustering object with c.labels['co_occ_linkage'] set to the final solution. 

        Examples
        --------
        To determine where the cut is visually, at threshold=0.5:

        >>> coMat = c.co_occurrence()
        >>> coMat.plot(threshold=0.5, linkage='ward')

        To create the cut at threshold=0.5 

        >>> cWard = c.co_occ_linkage(0.5, 'ward')
        >>> d.plot_data('parent', cluster_labels=cWard.labels['co_occ_linkage'])


        """
        params={}
        params['linkage'] = linkage
        params['threshold'] = threshold
        coMatObj = self.co_occurrence_matrix('parent')
        coL = finish.co_occurrence_linkage(coMatObj, threshold, linkage=linkage)
        coL.finish()
        c = oe.cluster(self.dataObj)
        name = 'co_occ_linkage'
        c.labels[name] = coL.labels
        c.params[name] = params
        c.data_source[name] = 'parent'
        c.clusterNumbers[name] = np.unique(c.labels[name])
        c.algorithms[name] = 'co_occ_linkage'
        return c

    def finish_graph_closure(self, threshold, clique_size = 3):
        """ 
        The finishing technique that treats the co-occurrence matrix as a graph, that is binarized by the threshold (>=threshold 
        becomes an unweighted, undirected edge in an adjacency matrix). This graph object is then subjected to clique formation
        according to clique_size (such as triangles if clique_size=3). The cliques are then combined in the graph to create unique
        cluster formations. 

        See also
        --------
        finishing.py 

        Returns
        -------
        c: openenembles clustering object
            New cluster object with final solution and name 'graph_closure'

        Examples
        --------
        >>> cGraph = c.finish_graph_closure(0.5, 3)
        >>> d.plot_data('parent', cluster_labels=cGraph.labels['graph_closure'])

        """
        params = {}
        params['threshold'] = threshold
        params['clique_size'] = clique_size
        coMatObj = self.co_occurrence_matrix('parent')

        c_G = finish.graph_closure(coMatObj.co_matrix, threshold, clique_size=clique_size)
        c_G.finish()
        c = oe.cluster(self.dataObj)
        name = 'graph_closure'
        c.labels[name] = c_G.labels
        c.params[name] = params
        c.data_source[name] = 'parent'
        c.clusterNumbers[name] = np.unique(c.labels[name])
        c.algorithms[name] = 'graph_closure'
        return c

    def finish_majority_vote(self, threshold=0.5):
        """

        Based on Ana Fred's 2001 paper: Fred, Ana. Finding Consistent Clusters in Data Partitions. In Multiple Classifier Systems, 
        edited by Josef Kittler and Fabio Roli, LNCS 2096, 309-18. Springer, 2001. 
        This algorithm assingns clusters to the same class if they co-cluster at least 50 of the time. It 
        greedily joins clusters with the evidence that at least one pair of items from two different clusters co-cluster 
        a majority of the time. Outliers will get their own cluster. 

        Parameters
        ----------
        threshold: float
            the threshold, or fraction of times objects co-cluster to consider a 'majority'. Default is 0.5 (50% of the time)

        Returns
        -------
        c: openensembles cluster object
            New cluster object with final solution and name 'majority_vote'

        Examples
        --------
        >>> c_MV = c.majority_vote(threshold=0.7)
        >>> labels = c_MV.labels['majority_vote']
        """
        params = {}
        coMatObj = self.co_occurrence_matrix('parent')
        c_MV = finish.majority_vote(coMatObj.co_matrix, threshold)
        c_MV.finish()

        c = oe.cluster(self.dataObj)
        name = 'majority_vote'
        c.labels[name] = c_MV.labels
        c.params[name] = params
        c.data_source[name] = 'parent'
        c.clusterNumbers[name] = np.unique(c.labels[name])
        c.algorithms[name] = 'majority_vote'
        return c


    def get_cluster_members(self, solution_name, clusterNum):
        """ Return the dataframe row indexes of a cluster number in solution named by solution_name 
        
        Parameters
        ----------
        solution_name: string
            the name of the clustering solution of interest
        clusterNum: int
            The cluster number of interest

        Returns
        -------
        indexes: list
            a list of indexes of objects with clusterNum in solution_name

        Examples
        --------
        Get a list of objects that belong to each cluster type in a solution

        >>> name = 'zscore_agglomerative_ward'
        >>> c.cluster('zscore', 'agglomerative', name, K=4, linkage='ward')
        >>> labels = {}
        >>> for i in c.clusterNumbers[name]:
        >>>     labels{i} = c.get_cluster_members(name, i)
        """
        indexes = np.where(self.labels[solution_name]==clusterNum)
        return indexes

    
    def search_field(self, field, value):
        """
        Find solutions that were made with 

        Parameters
        ----------
        field: string {'algorithm', 'data_source', 'K', 'linkage', 'distance', 'clusterNumber', etc.}
            The name of field, either in algorithm used, data_source selected, or a parameter passed to search for an exact value
        value: string or int
            The value to search for (where ints are passed for K (desired clusters) or clusterNumber (actual returned clusters))

        Returns
        -------
        names: list of strings
            The names of dictionary entries in clustering solutions matching field, value criteria. Returns empty list if nothing was found

        Raises
        ------
        ValueError
            If the field was not recognized.

        Examples
        --------
        Find all clustering solutions where K=2 was used
        >>> names = c.search_field('K', 2)

        Find all clustering solutions where the actual cluster numbers were 2
        >>> names = c.search_field('clusterNumber', 2)

        Find all solutions clustered using kmeans
        >>> names = c.search_field('algorithm', 'kmeans')

        Find all clustering solutions where ward linkage was used
        >>> names = c.search_field('linkage', 'ward')
        
        """
        names = []

        if field=='data_source':
            for name in list(self.data_source.keys()):
                if self.data_source[name]==value:
                    names.append(name)



        elif field == 'algorithm':
            for name in list(self.algorithms.keys()):
                if self.algorithms[name]==value:
                    names.append(name)


        elif field=='clusterNumber':
            for name in list(self.clusterNumbers.keys()):
                clusterNumber = len(self.clusterNumbers[name])
                if clusterNumber == value:
                    names.append(name)


        else: #otherwise, we're searching through the parameters
            paramFound = False
            for name in self.params.keys():
                params = self.params[name]
                if field in params.keys():
                    paramFound = True
                    if params[field] == value:
                        names.append(name)
            if not paramFound:
                raise ValueError("Field %s was not found in parameters of an clustering solutions"%(field))

        return names

    def slice(self, names):
        """
        Returns a new cluster object containing a slice indicated by the list of names given (dictionary keys shared amongst labels, params, etc.)

        Parameters
        ----------
        names: list
            A list of strings matching the names to keep in the new slice

        Returns
        --------
        c: an openensembles clustering object
            A oe.cluster object that contains only those names passed in

        Examples
        --------
        Get only the solutions made by agglomerative clustering

        >>> names = c.search_field('algorithm', 'agglomerative') #return all solutions with agglomerative
        >>> cNew = c.slice(names)

        Get only the solutions that were made with K=2 calls

        >>> names = c.search_field('K', 2) #return all solution names that used K=2
        >>> cNew = c.slice(names)

        Raises
        ------
        ValueError
            If a name in the list of names does not exist in cluster object


        """
        c = oe.cluster(self.dataObj)
        names_existing = list(self.labels.keys())
        for name in names:
            if name not in names_existing:
                raise ValueError("ERROR: the source you requested for slicing does not exist in cluster object %s"%(name))
            c.labels[name] = self.labels[name]
            c.data_source[name] = self.data_source[name]
            c.params[name] = self.params[name]
            c.clusterNumbers[name] = self.clusterNumbers[name]
            c.algorithms[name] = self.algorithms[name]
        return c



class validation:
    """
    validation is a class to calculate any number of validation metrics on clustering solutions in data. 
    An individual validation metric must be called on a particular instantiation of the data matrix (like 'parent' or 'zscore')
    and a specific solution in cObj. 
    """
    def __init__(self, dataObj, cObj):
        """ instantiate the object to create a dictionary of validation measurements """
        self.dataObj = dataObj 
        self.cObj = cObj
        self.validation = {} #key here is the name like HC_parent for hierarchically clustered parent
        self.source_name = {}
        self.cluster_name = {}
        self.description = {} #here is a quick description of the validation metric

    def validation_metrics_available(self):
        """ Return all available validation metrics """ 
        validation = val.validation(self.dataObj.D['parent'], [])
        FCN_DICT = validation.validation_metrics_available()
        return FCN_DICT


    def calculate(self, validation_name, cluster_name, source_name='parent'):
        """
        Calls the function titled by validation_name on the data matrix set by source_name (default 'parent') and clustering solution by cluster_name
        Appends to validation with key value equal to the validation_name+source_name+cluster_name

        Returns
        -------
        output_name: str
            The handle name for accessing validation results
        """

        output_name = "%s_%s_%s"%(validation_name, source_name, cluster_name)

        #check that the validation has not already been calcluated
        if output_name in self.validation:
            warnings.warn('Validation of type requested already exists and will not be added to validation dictionary', UserWarning)
            return

        #CHECK that the source exists
        if source_name not in self.dataObj.D:
            raise ValueError("ERROR: the source you requested for validation does not exist by that name %s"%(source_name))
        if cluster_name not in self.cObj.labels:
            raise ValueError("ERROR: the clustering solution you requested for validation does not exist by the name %s"%(source_name))
        
        FCN_DICT = self.validation_metrics_available()
        
        if validation_name not in FCN_DICT:
            raise ValueError( "The validation metric you requested does not exist, currently the following are supported %s"%(list(FCN_DICT.keys())))
 
        v = val.validation(self.dataObj.D[source_name], self.cObj.labels[cluster_name])
        func = getattr(v,validation_name)
        func()
 
        
        self.validation[output_name] = v.validation
        self.description[output_name] = v.description
        self.source_name[output_name] = source_name
        self.cluster_name[output_name] = cluster_name

        return output_name



