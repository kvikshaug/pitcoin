# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Block.nonce'
        db.alter_column(u'db_block', 'nonce', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'Block.bits'
        db.alter_column(u'db_block', 'bits', self.gf('django.db.models.fields.BigIntegerField')())

    def backwards(self, orm):

        # Changing field 'Block.nonce'
        db.alter_column(u'db_block', 'nonce', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'Block.bits'
        db.alter_column(u'db_block', 'bits', self.gf('django.db.models.fields.IntegerField')())

    models = {
        u'db.block': {
            'Meta': {'object_name': 'Block'},
            'bits': ('django.db.models.fields.BigIntegerField', [], {}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merkle_root': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'nonce': ('django.db.models.fields.BigIntegerField', [], {}),
            'prev_block': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['db.Block']", 'null': 'True'}),
            'prev_hash': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['db']