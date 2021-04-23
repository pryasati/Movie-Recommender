"""Rating data layer object module.

This module provides low level access to data layer rating dataset handling.
"""
import pandas as pd
import numpy as np


class RatingData:
    def __init__(self, df_data = None, df_ratmat = None, df_app_data = None):
        """Constructor, reads dataset files or use given dataset for rating and matrix information.

        Args:
            df_data: custom rating information dataset
            df_ratmat: custom user x movie rating information dataset
            df_app_data: custom app user rating information dataset
        """
        # base rating information dataset
        if df_data is None:
            # use base dataset read from file
            self.df_data = pd.read_csv(
                "movielens/Movielens-02/u.data",
                delimiter="\t",
                names=['user_id', 'item_id', 'rating', 'timestamp'])
        else:
            # use given custom dataset
            self.df_data = df_data
        
        # user x movie rating information dataset
        if df_ratmat is None:
            # use base dataset read from file
            self.df_ratmat = pd.read_csv(
                "movielens/Movielens-02/data_matrix.csv", index_col=0)
        else:
            # use given custom dataset
            self.df_ratmat = df_ratmat

        # app user rating information dataset
        if df_app_data is None:
            # use base dataset read from file
            try:
                self.df_app_data = pd.read_csv("app_data.csv")
            except FileNotFoundError as e:
                # start with empty set, if not found
                self.df_app_data = pd.DataFrame(
                    columns=['user_id', 'item_id', 'rating', 'timestamp'])
        else:
             # use given custom dataset
            self.df_app_data = df_app_data

    def get_valid_user_ratings(self, user_id):
        """Finds valid (> 0) ratings for given user.

        Args:
            user_id: unique user id

        Returns:
            A data frame for user_id, item_id, rating
        """
        return self.df_app_data.loc[(self.df_app_data["user_id"] == int(user_id)) & (self.df_app_data["rating"].isna() == False)]

    def get_user_ratings_by_movie(self, movie_id):
        """Finds valid (> 0) ratings for given movie.

        Args:
            movie_id: unique user id

        Returns:
            A data frame for user x ratings matrix
        """
        return self.df_ratmat[self.df_ratmat.iloc[:, movie_id - 1] > 0]

    def get_user_vector(self, user_id):
        """Builds the same row format of user rating matrix by app user ratings.

        Args:
            user_id: unique user id

        Returns:
            A data frame representing user rating vector
        """
        if user_id in self.df_ratmat.index:
            # user from base dataset
            return np.array([self.df_ratmat.loc[user_id]])
        # construct a vector out of app user rating data
        movies_rated = self.get_valid_user_ratings(user_id)
        movie_size = self.df_ratmat.shape[1]
        cols = [str(i) for i in range(1, movie_size + 1)]
        df = pd.DataFrame(columns=cols)
        new_row = {}
        for i, r in movies_rated[['item_id', 'rating']].iterrows():
            new_row[str(int(r['item_id']))] = int(r['rating'])
        df = df.append(new_row, ignore_index=True)
        # mark 0 (=not rated) if not rated by the user
        return df.fillna(0)

    def get_most_watched_movie_index(self, user_id, count):
        """Finds most watched(rated) movies of specified counts and not rated by the given user.

        Args:
            user_id: user id (not index of the table)
            count: number of movies to get

        Returns:
            A list of movie index not rated by user.
        """
        # find most watched movie by 0 rating count on each movie,
        # then sorted out increasing order which indicates which movie has least 0 ratings
        # meaning most watched movie.
        zero_ratings = self.df_ratmat.apply(pd.Series.value_counts).iloc[0, 1:]
        user_rated_movies = self.get_user_ratings(user_id)["item_id"]
        most_watched_movies_not_rated = zero_ratings[
            zero_ratings.index.isin(user_rated_movies.astype(int).astype(str)) != True].sort_values().head(count)
        return most_watched_movies_not_rated.index

    def save(self):
        """Store all the app user ratings into app data files."""
        self.df_app_data = self.df_app_data.to_csv("app_data.csv", index=False)

    def add_user_rating(self, user_id, movie_id, rating):
        """Adds a rating input from user into app dataset.

        Args:
            user_id: user id (not index of the table)
            movie_id: movie id (not index of the table)
            rating: rating (0 - 5)
        """
        new_row = {'user_id': int(user_id), 'item_id': int(movie_id), 'rating': rating}
        self.df_app_data = self.df_app_data.append(new_row, ignore_index=True)

    def get_average_ratings_of_movies(self, movie_ids):
        """Calculates a mean ratings for given movies.

        Args:
            movie_ids: list of movie ids
        
        Returns:
            Mean ratings for given movies
        """
        return self.df_data[self.df_data["item_id"].isin(movie_ids)].groupby("item_id").mean()


    def get_user_ratings(self, user_id):
        """Finds valid (> 0) ratings for given user in the app data including NaN values.

        Args:
            user_id: unique user id

        Returns:
            A data frame for user_id, item_id, rating
        """
        return self.df_app_data.loc[(self.df_app_data["user_id"] == int(user_id))]