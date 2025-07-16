#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMDb数据转换脚本
创建示例CSV文件用于测试
"""

import csv

def create_sample_csv_files():
    """创建示例CSV文件用于测试"""
    
    # 创建一些基本的CSV文件
    csv_files = {
        'name.csv': [
            ['id', 'name', 'imdb_index', 'imdb_id', 'gender', 'name_pcode_cf', 'name_pcode_nf', 'surname_pcode', 'md5sum'],
            ['1', 'John Doe', 'J', '12345', 'M', 'J500', 'J500', 'D000', 'abc123'],
            ['2', 'Jane Smith', 'J', '12346', 'F', 'J500', 'J500', 'S530', 'def456']
        ],
        'title.csv': [
            ['id', 'title', 'imdb_index', 'kind_id', 'production_year', 'imdb_id', 'phonetic_code', 'episode_of_id', 'season_nr', 'episode_nr', 'series_years', 'md5sum'],
            ['1', 'Sample Movie', 'S', '1', '2020', '12345', 'S514', 'NULL', 'NULL', 'NULL', 'NULL', 'abc123'],
            ['2', 'Another Movie', 'A', '1', '2021', '12346', 'A536', 'NULL', 'NULL', 'NULL', 'NULL', 'def456']
        ],
        'link_type.csv': [
            ['id', 'link'],
            ['1', 'follows'],
            ['2', 'followed by'],
            ['3', 'features'],
            ['4', 'featured in'],
            ['5', 'spoofs'],
            ['6', 'spoofed in'],
            ['7', 'references'],
            ['8', 'referenced in'],
            ['9', 'similar to'],
            ['10', 'remake of'],
            ['11', 'remade as'],
            ['12', 'spin-off from'],
            ['13', 'spin-off'],
            ['14', 'other']
        ],
        'kind_type.csv': [
            ['id', 'kind'],
            ['1', 'movie'],
            ['2', 'tv series'],
            ['3', 'tv movie'],
            ['4', 'video movie'],
            ['5', 'tv episode'],
            ['6', 'video game'],
            ['7', 'tv mini series']
        ],
        'company_type.csv': [
            ['id', 'kind'],
            ['1', 'production companies'],
            ['2', 'distributors'],
            ['3', 'special effects companies'],
            ['4', 'other companies']
        ],
        'comp_cast_type.csv': [
            ['id', 'kind'],
            ['1', 'cast'],
            ['2', 'crew']
        ],
        'info_type.csv': [
            ['id', 'info'],
            ['1', 'genres'],
            ['2', 'plot summary'],
            ['3', 'taglines'],
            ['4', 'trivia'],
            ['5', 'goofs'],
            ['6', 'soundtracks'],
            ['7', 'quotes'],
            ['8', 'release dates'],
            ['9', 'languages'],
            ['10', 'countries'],
            ['11', 'color info'],
            ['12', 'aspect ratio'],
            ['13', 'sound mix'],
            ['14', 'certificates'],
            ['15', 'locations'],
            ['16', 'technical'],
            ['17', 'literature'],
            ['18', 'business'],
            ['19', 'crazy credits'],
            ['20', 'alternate versions'],
            ['21', 'connections'],
            ['22', 'editing'],
            ['23', 'costume design'],
            ['24', 'make up'],
            ['25', 'production design'],
            ['26', 'art direction'],
            ['27', 'cinematography'],
            ['28', 'film editing'],
            ['29', 'casting'],
            ['30', 'production management'],
            ['31', 'sound department'],
            ['32', 'special effects'],
            ['33', 'visual effects'],
            ['34', 'stunts'],
            ['35', 'electrical department'],
            ['36', 'camera department'],
            ['37', 'animation department'],
            ['38', 'casting department'],
            ['39', 'costume department'],
            ['40', 'editorial department'],
            ['41', 'location management'],
            ['42', 'music department'],
            ['43', 'transportation department'],
            ['44', 'miscellaneous'],
            ['45', 'thanks'],
            ['46', 'other']
        ],
        'role_type.csv': [
            ['id', 'role'],
            ['1', 'actor'],
            ['2', 'actress'],
            ['3', 'producer'],
            ['4', 'writer'],
            ['5', 'director'],
            ['6', 'composer'],
            ['7', 'cinematographer'],
            ['8', 'editor'],
            ['9', 'production_designer'],
            ['10', 'costume_designer'],
            ['11', 'miscellaneous']
        ]
    }
    
    # 创建CSV文件
    for filename, data in csv_files.items():
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='|')
            writer.writerows(data)
        print(f"Created {filename}")

def create_empty_csv_files():
    """创建空的CSV文件"""
    
    # 需要创建的所有CSV文件
    csv_files = [
        'aka_name.csv', 'aka_title.csv', 'cast_info.csv', 'char_name.csv',
        'company_name.csv', 'complete_cast.csv', 'keyword.csv', 'movie_companies.csv',
        'movie_info.csv', 'movie_info_idx.csv', 'movie_keyword.csv', 'movie_link.csv',
        'person_info.csv'
    ]
    
    for filename in csv_files:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='|')
            # 写入表头（根据SQL文件中的表结构）
            if filename == 'aka_name.csv':
                writer.writerow(['id', 'person_id', 'name', 'imdb_index', 'name_pcode_cf', 'name_pcode_nf', 'surname_pcode', 'md5sum'])
            elif filename == 'aka_title.csv':
                writer.writerow(['id', 'movie_id', 'title', 'imdb_index', 'kind_id', 'production_year', 'phonetic_code', 'episode_of_id', 'season_nr', 'episode_nr', 'note', 'md5sum'])
            elif filename == 'cast_info.csv':
                writer.writerow(['id', 'person_id', 'movie_id', 'person_role_id', 'note', 'nr_order', 'role_id'])
            elif filename == 'char_name.csv':
                writer.writerow(['id', 'name', 'imdb_index', 'imdb_id', 'name_pcode_nf', 'surname_pcode', 'md5sum'])
            elif filename == 'company_name.csv':
                writer.writerow(['id', 'name', 'country_code', 'imdb_id', 'name_pcode_nf', 'name_pcode_sf', 'md5sum'])
            elif filename == 'complete_cast.csv':
                writer.writerow(['id', 'movie_id', 'subject_id', 'status_id'])
            elif filename == 'keyword.csv':
                writer.writerow(['id', 'keyword', 'phonetic_code'])
            elif filename == 'movie_companies.csv':
                writer.writerow(['id', 'movie_id', 'company_id', 'company_type_id', 'note'])
            elif filename == 'movie_info.csv':
                writer.writerow(['id', 'movie_id', 'info_type_id', 'info', 'note'])
            elif filename == 'movie_info_idx.csv':
                writer.writerow(['id', 'movie_id', 'info_type_id', 'info', 'note'])
            elif filename == 'movie_keyword.csv':
                writer.writerow(['id', 'movie_id', 'keyword_id'])
            elif filename == 'movie_link.csv':
                writer.writerow(['id', 'movie_id', 'linked_movie_id', 'link_type_id'])
            elif filename == 'person_info.csv':
                writer.writerow(['id', 'person_id', 'info_type_id', 'info', 'note'])
        
        print(f"Created empty {filename}")

if __name__ == "__main__":
    print("Creating sample CSV files for IMDb database...")
    create_empty_csv_files()
    print("Done! You can now run the SQL script to create the database.") 