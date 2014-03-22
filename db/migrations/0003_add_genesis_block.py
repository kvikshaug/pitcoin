# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        genesis_block = orm['db.Block'](
            version=1,
            prev_hash='0000000000000000000000000000000000000000000000000000000000000000',
            merkle_root='4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b',
            timestamp=datetime.datetime.utcfromtimestamp(1296688602),
            bits=486604799,
            nonce=414098458,
            height=0,
            prev_block=None,
        )
        genesis_block.save()

    def backwards(self, orm):
        orm['db.Block'].objects.all().delete()

    models = {
        u'db.block': {
            'Meta': {'object_name': 'Block'},
            'bits': ('django.db.models.fields.IntegerField', [], {}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merkle_root': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'nonce': ('django.db.models.fields.IntegerField', [], {}),
            'prev_block': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['db.Block']", 'null': 'True'}),
            'prev_hash': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['db']
    symmetrical = True
