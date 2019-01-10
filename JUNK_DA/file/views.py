from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import boto3
from django.http import FileResponse
import string

# Create your views here.


# 文件操作
class FileOperate:
    def __init__(self):
        self.aws_key = 'id'
        self.aws_secret = 'secret'
        self.region = 'region'
        self.bucket = 'bucket_name'
        self.session = boto3.Session(
            aws_access_key_id=self.aws_key,
            aws_secret_access_key=self.aws_secret,
            region_name=self.region
        )

    # 获取文件信息函数
    def _getFiles(self, userId):
        client = self.session.client('s3')
        response = client.list_objects(
            Bucket=self.bucket,
            Prefix=userId
        )
        s3 = self.session.resource('s3')
        bucket = s3.Bucket(self.bucket)
        if 'Contents' not in response.keys():
            return []
        else:
            files = []
            contents = response['Contents']
            for i in range(len(contents)):
                name = contents[i]['Key'].split('/')[1]
                versions = bucket.object_versions.filter(
                    Prefix=userId + '/' + name
                )
                children = []
                for version in versions:
                    obj = version.get()
                    children_dic = {
                        'key': name + '/' + obj.get('VersionId'),
                        'filename': '历史版本',
                        'size': str(
                            round(obj.get('ContentLength') / 1024)
                        ) + 'KB',
                        'versionId': obj.get('VersionId'),
                        'lastModified': str(obj.get(
                            'LastModified')).split('+')[0],
                    }
                    children.append(children_dic)
                dic = {}
                dic['key'] = children[0]['key']
                dic['filename'] = name
                dic['size'] = str(
                    round(contents[i]['Size'] / 1024)
                ) + 'KB'
                dic['versionId'] = children[0]['versionId']
                dic['lastModified'] = children[0]['lastModified']
                if len(children) == 1:
                    files.append(dic)
                else:
                    children.pop(0)
                    dic['children'] = children
                    files.append(dic)
            return files

    # 文件概览
    def files_overview(self, request):
        userId = request.GET.get('userId')
        try:
            files = self._getFiles(userId)
            dic = {'status': 1, 'data': files}
            dic = json.dumps(dic, ensure_ascii=False)
            return HttpResponse(dic)
        except Exception as e:
            dic = {'status': 0, 'message': str(e)}
            dic = json.dumps(dic, ensure_ascii=False)
            return HttpResponse(dic)

    # 上传
    @csrf_exempt
    def upload(self, request):
        chinese_punctuation = "，。、？~！@#￥%……&*（）——【】|：；‘’“”、《》-=+·"
        punctuation = list(string.punctuation) + list(chinese_punctuation)
        userId = request.GET.get('userId')
        if request.method == 'POST':
            f_obj = request.FILES['file']
        client = self.session.client('s3')
        response = client.list_objects(
            Bucket=self.bucket,
            Prefix=userId
        )
        if 'Contents' not in response or len(response['Contents'])-1 < 5:
            if f_obj.name.split('.')[-1] not in ['csv', 'xlsx']:
                dic = {'status': 0, 'message': '非法文件格式'}
                dic = json.dumps(dic, ensure_ascii=False)
                return HttpResponse(dic)
            elif f_obj.size > 5000000:
                dic = {'status': 0, 'message': '文件过大'}
                dic = json.dumps(dic, ensure_ascii=False)
                return HttpResponse(dic)
            else:
                filename_lst = f_obj.name.split('.')
                suffix = filename_lst.pop()
                filename = ''.join(filename_lst)
                filename = ''.join(
                    [i for i in filename if i not in punctuation]
                )
                key = userId + '/' + filename + '.' + suffix
                try:
                    response = client.put_object(
                        Key=key,
                        Body=f_obj.read(),
                        Bucket=self.bucket
                    )
                    dic = {
                        'status': 1,
                        'data': self._getFiles(userId)
                    }
                    dic = json.dumps(dic, ensure_ascii=False)
                    return HttpResponse(dic)
                except Exception as e:
                    dic = {'status': '0', 'message': str(e)}
                    dic = json.dumps(dic, ensure_ascii=False)
                    return HttpResponse(dic)
        else:
            dic = {'status': 0, 'message': '文件个数已达上限'}
            dic = json.dumps(dic, ensure_ascii=False)
            return HttpResponse(dic)

    # 下载
    @csrf_exempt
    def download(self, request):
        req = json.loads(request.body)
        userId = req['userId']
        filename = req['filename'].split('.')[0]
        suffix = req['filename'].split('.')[1]
        versionId = req['versionId']
        client = self.session.client('s3')
        key = userId + '/' + filename + '.' + suffix
        try:
            response = client.get_object(
                Bucket=self.bucket,
                Key=key,
                VersionId=versionId
            )
            file_obj = response['Body']
            res = FileResponse(file_obj)
            res['Content-Type'] = 'application/octet-stream'
            res['Content-Disposition'] = 'attachment; \
            filename={0}-{1}.{2}'.format(filename, versionId, suffix)
            return res
        except Exception as e:
            dic = {'status': 0, 'message': str(e)}
            dic = json.dumps(dic, ensure_ascii=False)
            return HttpResponse(dic)

    # 删除
    @csrf_exempt
    def delete(self, request):
        req = json.loads(request.body)
        userId = req['userId']
        files = req['files']
        objects = []
        for _file in files:
            _object = {
                'Key': userId + '/' + _file['filename'],
                'VersionId': _file['versionId']
            }
            objects.append(_object)
        client = self.session.client('s3')
        try:
            client.delete_objects(
                Bucket=self.bucket, Delete={'Objects': objects}
            )
            dic = {'status': 1, 'data': self._getFiles(userId)}
            dic = json.dumps(dic, ensure_ascii=False)
            return HttpResponse(dic)
        except Exception as e:
            dic = {'status': 0, 'message': str(e)}
            dic = json.dumps(dic, ensure_ascii=False)
            return HttpResponse(dic)
